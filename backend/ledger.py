import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation
import pandas as pd
import matplotlib.pyplot as plt
import os

# Import centralized modules using relative imports
from . import persistence as db
from . import documents as db_docs

def _get_movimenti():
    """Helper to load all financial transactions."""
    return db.load_data(db.PRIMANOTA_DB)

def _save_movimenti(movimenti):
    """Helper to save all financial transactions."""
    db.save_data(db.PRIMANOTA_DB, movimenti)

def create_movimento(data):
    """
    Creates a new manual financial transaction (income or expense).
    
    Args:
        data (dict): A dict containing: date, type ('Entrata'/'Uscita'), 
                     description, amount_netto, amount_iva, amount_ritenuta, 
                     amount_totale, notes.

    Returns:
        tuple (bool, str): (True, "Success message") or (False, "Error message").
    """
    try:
        # Ensure correct types
        movimento = {
            'id': str(uuid.uuid4()),
            'date': data['date'], # YYYY-MM-DD
            'type': data['type'],
            'description': data['description'],
            'amount_netto': Decimal(str(data.get('amount_netto', '0'))),
            'amount_iva': Decimal(str(data.get('amount_iva', '0'))),
            'amount_ritenuta': Decimal(str(data.get('amount_ritenuta', '0'))),
            'amount_totale': Decimal(str(data.get('amount_totale', '0'))),
            'linked_invoice_id': data.get('linked_invoice_id', None),
            'notes': data.get('notes', '')
        }
    except InvalidOperation as e:
        return False, f"Errore nei dati numerici: {e}"
    except Exception as e:
        return False, f"Errore nella validazione dei dati: {e}"

    movimenti = _get_movimenti()
    movimenti.append(movimento)
    _save_movimenti(movimenti)
    return True, "Movimento registrato con successo."

def create_movimento_from_invoice(invoice_id, payment_date):
    """
    Creates an 'Entrata' (income) transaction linked to an invoice.
    This function also updates the invoice status to 'Pagato'.

    Args:
        invoice_id (str): The 'id' of the invoice being paid.
        payment_date (str): The date of payment in 'YYYY-MM-DD' format.

    Returns:
        tuple (bool, str): (True, "Success message") or (False, "Error message").
    """
    # 1. Find the invoice
    invoice = db_docs.find_document_by_id(invoice_id)
    if not invoice:
        return False, "Fattura non trovata."
    if invoice['status'] == 'Pagato':
        return False, "Fattura già registrata come pagata."
        
    # 2. Update invoice status
    success, _ = db_docs.update_document_status(invoice_id, 'Pagato')
    if not success:
        return False, "Errore nell'aggiornamento dello stato fattura."

    # 3. Create the linked transaction
    movimento_data = {
        'date': payment_date,
        'type': 'Entrata',
        'description': f"Incasso Fattura N. {invoice['number']}",
        'amount_netto': invoice['taxable_amount'],
        'amount_iva': invoice['vat_amount'],
        'amount_ritenuta': invoice.get('ritenuta_amount', Decimal('0')),
        # The amount received is the 'total_da_pagare'
        'amount_totale': invoice.get('total_da_pagare', invoice['total']), 
        'linked_invoice_id': invoice_id,
        'notes': f"Rif. Cliente ID: {invoice['client_id']}"
    }
    
    return create_movimento(movimento_data)

def delete_movimento(movimento_id):
    """
    Deletes a transaction.
    If it was linked to an invoice, it resets the invoice status to 'In sospeso'.

    Args:
        movimento_id (str): The 'id' of the transaction to delete.

    Returns:
        tuple (bool, str): (True, "Success message") or (False, "Error message").
    """
    movimenti = _get_movimenti()
    movimento_found = None
    new_movimenti = []
    
    for m in movimenti:
        if m['id'] == movimento_id:
            movimento_found = m
        else:
            new_movimenti.append(m)
            
    if not movimento_found:
        return False, "Movimento non trovato."
        
    # If linked, reset invoice status to 'In sospeso'
    linked_id = movimento_found.get('linked_invoice_id')
    if linked_id:
        try:
            # We don't care if it fails (e.g., invoice was deleted)
            db_docs.update_document_status(linked_id, 'In sospeso')
        except Exception as e:
            print(f"Warning: could not reset invoice {linked_id}. {e}")

    _save_movimenti(new_movimenti)
    return True, "Movimento eliminato."

def get_movimenti(start_date, end_date):
    """
    Gets all transactions within a date range.

    Args:
        start_date (datetime.date): The start of the date range.
        end_date (datetime.date): The end of the date range.

    Returns:
        list: A sorted list of transaction dictionaries.
    """
    movimenti = _get_movimenti()
    results = []
    
    for m in movimenti:
        try:
            m_date = datetime.strptime(m['date'], '%Y-%m-%d').date()
            if start_date <= m_date <= end_date:
                results.append(m)
        except ValueError:
            continue
            
    return sorted(results, key=lambda x: x['date'])

def _get_dataframe(year):
    """
    Helper to load all transactions for a year into a pandas DataFrame.
    Converts Decimal/date types to formats pandas can use (float/datetime).

    Args:
        year (int): The year to load.

    Returns:
        tuple (pd.DataFrame, str): (DataFrame, "Status message").
    """
    movimenti = _get_movimenti()
    if not movimenti:
        return pd.DataFrame(columns=['date']), "Nessun movimento trovato."
        
    df = pd.DataFrame(movimenti)
    
    # Convert types for pandas
    df['date'] = pd.to_datetime(df['date'])
    for col in ['amount_netto', 'amount_iva', 'amount_ritenuta', 'amount_totale']:
        # Convert Decimal to float
        df[col] = df[col].apply(lambda x: float(x))
        
    # Filter by year
    df_year = df[df['date'].dt.year == year].copy()
    if df_year.empty:
        return pd.DataFrame(columns=['date']), f"Nessun movimento trovato per l'anno {year}."
        
    df_year.set_index('date', inplace=True)
    return df_year, "Dati caricati."

def generate_monthly_stats(year):
    """
    Generates monthly statistics (Income/Expense) for a given year.

    Args:
        year (int): The year to analyze.

    Returns:
        tuple (pd.DataFrame, str): (Stats DataFrame, "Status message").
    """
    df, msg = _get_dataframe(year)
    if df.empty:
        return pd.DataFrame(), msg

    # Resample by Month End ('ME') and sum
    entrate = df[df['type'] == 'Entrata']['amount_totale'].resample('ME').sum()
    uscite = df[df['type'] == 'Uscita']['amount_totale'].resample('ME').sum()
    
    # Combine, rename, and clean
    stats_df = pd.DataFrame({'Entrate': entrate, 'Uscite': uscite})
    stats_df.index.name = 'Mese'
    stats_df.index = stats_df.index.strftime('%Y-%m') # Format index
    stats_df = stats_df.fillna(0) # Replace NaN with 0
    
    # Add a total row
    stats_df.loc['TOTALE'] = stats_df.sum()
    
    return stats_df, "Statistiche generate."

def plot_monthly_stats(stats_df, filename):
    """
    Saves a bar chart of monthly stats to a file.
    'stats_df' should be the DataFrame from generate_monthly_stats.

    Args:
        stats_df (pd.DataFrame): The statistics data.
        filename (str): The path to save the .png file.

    Returns:
        tuple (bool, str): (True, "Success message") or (False, "Error message").
    """
    try:
        # Remove 'TOTALE' row if it exists, for plotting
        stats_to_plot = stats_df.drop('TOTALE', errors='ignore')

        if stats_to_plot.empty:
            return False, "Nessun dato da plottare."

        ax = stats_to_plot.plot(kind='bar', figsize=(12, 7), rot=45)
        
        # Add titles and labels
        ax.set_title(f"Riepilogo Entrate/Uscite Mensili", fontsize=16)
        ax.set_ylabel("Importo (€)")
        ax.set_xlabel("Mese")
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Save the figure
        plt.tight_layout()
        plt.savefig(filename)
        plt.close() # Close the plot to free memory
        
        return True, f"Grafico salvato come {filename}"
    except Exception as e:
        return False, f"Errore during la generazione del grafico: {e}"

def export_per_commercialista(filename, year, format='csv'):
    """
    Exports all transactions for a given year to CSV or Excel
    in a format suitable for an accountant.

    Args:
        filename (str): The target file name.
        year (int): The year to export.
        format (str): 'csv' or 'excel'.

    Returns:
        tuple (bool, str): (True, "Success message") or (False, "Error message").
    """
    df, msg = _get_dataframe(year)
    if df.empty:
        return False, msg

    # Select and rename columns for the accountant
    export_df = df[[
        'type', 'description', 'amount_netto', 'amount_iva', 
        'amount_ritenuta', 'amount_totale', 'linked_invoice_id', 'notes'
    ]].copy()
    
    export_df.rename(columns={
        'type': 'Tipo (E/U)',
        'description': 'Descrizione',
        'amount_netto': 'Imponibile',
        'amount_iva': 'IVA',
        'amount_ritenuta': 'Ritenuta',
        'amount_totale': 'Totale Pagato/Incassato',
        'linked_invoice_id': 'Rif. Fattura ID',
        'notes': 'Note'
    }, inplace=True)
    
    # Reset index to make 'date' a column again
    export_df.reset_index(inplace=True)
    export_df.rename(columns={'date': 'Data'}, inplace=True)
    
    try:
        if format == 'csv':
            # Use semicolon separator and comma decimal for Italian locale
            export_df.to_csv(filename, index=False, encoding='utf-8-sig', sep=';', decimal=',')
            msg = f"Esportazione CSV completata: {filename}"
        elif format == 'excel':
            export_df.to_excel(filename, index=False)
            msg = f"Esportazione Excel completata: {filename}"
        else:
            return False, "Formato non supportato."
            
        return True, msg
    except Exception as e:
        return False, f"Errore durante l'esportazione: {e}"