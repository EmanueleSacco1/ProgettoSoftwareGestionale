import uuid
from datetime import datetime, timedelta

# Import centralized modules using relative imports
from . import persistence as db
from . import email_utils
from . import projects as db_progetti
from . import documents as db_docs

def _parse_date(date_str):
    """
    Helper to safely parse an ISO date string ('YYYY-MM-DD') into a date object.

    Args:
        date_str (str): The date string.

    Returns:
        datetime.date: The parsed date object, or None if parse fails.
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None

def get_eventi(start_date, end_date):
    """
    Gets all calendar events (manual and automatic) within a date range.

    Args:
        start_date (datetime.date): The start of the date range.
        end_date (datetime.date): The end of the date range.

    Returns:
        list: A sorted list of event dictionaries.
    """
    events = db.load_data(db.CALENDARIO_DB)
    results = []
    
    for event in events:
        event_date = _parse_date(event.get('date'))
        # Check if the event's date falls within the specified range
        if event_date and start_date <= event_date <= end_date:
            results.append(event)
            
    # Sort results by date
    return sorted(results, key=lambda x: x['date'])

def create_evento_manuale(event_date, title, description):
    """
    Adds a new user-created event to the calendar database.

    Args:
        event_date (str): The date in 'YYYY-MM-DD' format.
        title (str): The title of the event.
        description (str): A description for the event.

    Returns:
        tuple (bool, str): (True, "Success message") or (False, "Error message").
    """
    if not _parse_date(event_date):
        return False, "Data non valida. Usare YYYY-MM-DD."
        
    event = {
        'id': str(uuid.uuid4()),
        'date': event_date,
        'title': title,
        'description': description,
        'type': 'manuale', # Distinguish from automatic events
        'source_id': None
    }
    
    events = db.load_data(db.CALENDARIO_DB)
    events.append(event)
    db.save_data(db.CALENDARIO_DB, events)
    return True, "Evento creato."

def generate_scadenze_automatiche():
    """
    Scans all projects and invoices to generate/update calendar events.
    This function is 'idempotent' - it deletes all old 'auto' events
    and regenerates them, ensuring no duplicates.
    """
    all_events = db.load_data(db.CALENDARIO_DB)
    
    # 1. Filter to keep only manual events
    manual_events = [e for e in all_events if e.get('type') == 'manuale']
    
    new_auto_events = []
    
    # 2. Scan active projects for incomplete phases with due dates
    progetti = db_progetti.get_all_projects()
    for p in progetti:
        if p.get('status') == 'In corso':
            for fase in p.get('fasi', []):
                if not fase.get('completata') and fase.get('scadenza'):
                    fase_date = _parse_date(fase['scadenza'])
                    if fase_date:
                        new_auto_events.append({
                            'id': str(uuid.uuid4()),
                            'date': fase['scadenza'],
                            'title': f"[PROGETTO] Scadenza Fase: {fase['nome']}",
                            'description': f"Progetto: {p['name']} (ID: {p['id']})",
                            'type': 'auto_project',
                            'source_id': p['id']
                        })

    # 3. Scan 'In sospeso' or 'Scaduto' invoices for due dates
    fatture = db_docs.get_all_documents(doc_type='invoice')
    for f in fatture:
        if f.get('status') == 'In sospeso' or f.get('status') == 'Scaduto':
            due_date_str = f.get('due_date')
            due_date = _parse_date(due_date_str)
            if due_date:
                new_auto_events.append({
                    'id': str(uuid.uuid4()),
                    'date': due_date_str,
                    'title': f"[FATTURA] Scadenza Pagamento: {f['number']}",
                    'description': f"Cliente (ID: {f['client_id']}) - Totale: {f.get('total_da_pagare', f.get('total', 0)):.2f} €",
                    'type': 'auto_invoice',
                    'source_id': f['id']
                })
                
    # 4. Save the new combined list
    final_events = manual_events + new_auto_events
    db.save_data(db.CALENDARIO_DB, final_events)
    
    return len(new_auto_events), "Scadenze automatiche aggiornate."

def send_notifiche_scadenze(giorni_anticipo=1):
    """
    Finds all deadlines for a target date (e.g., tomorrow)
    and sends a single summary email.

    Args:
        giorni_anticipo (int): How many days in the future to check.
                             1 = tomorrow.

    Returns:
        tuple (bool, str): (True, "Success/Info message") or (False, "Error message").
    """
    settings = db.load_settings()
    smtp_config = settings.get('smtp_config')
    notify_email = smtp_config.get('notify_email', smtp_config.get('user'))

    if not notify_email:
        return False, "Nessuna email per le notifiche impostata nei settings."
    if not smtp_config.get('host') or not smtp_config.get('user'):
        return False, "Configurazione SMTP incompleta nei settings."
        
    # Calculate the target date
    target_date = datetime.now().date() + timedelta(days=giorni_anticipo)
    target_date_str = target_date.isoformat()

    # Find events for that specific day
    # We use generate_scadenze_automatiche() first to ensure data is fresh
    generate_scadenze_automatiche()
    all_events = db.load_data(db.CALENDARIO_DB)
    events_for_target_date = [e for e in all_events if e.get('date') == target_date_str]
    
    if not events_for_target_date:
        return True, f"Nessuna scadenza trovata per {target_date_str}."

    # Build the email body
    subject = f"Promemoria Scadenze per {target_date_str}"
    body = f"Ciao,\n\nQuesti sono i tuoi promemoria per {target_date_str}:\n\n"
    
    for event in events_for_target_date:
        body += "---------------------------------\n"
        body += f"OGGETTO: {event['title']}\n"
        body += f"DETTAGLI: {event['description']}\n"
    
    body += "\n\nBuon lavoro,\nIl Tuo Gestionale"
    
    # Send the email using the utility function
    success, msg = email_utils.send_email(
        recipient_email=notify_email,
        subject=subject,
        body=body,
        smtp_config=smtp_config
    )
    
    return success, msg