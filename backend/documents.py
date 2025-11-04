import os
import uuid
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

# Import for new HTML->PDF generation
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

# Required for stats
import pandas as pd

# Import centralized modules using relative imports
from . import persistence as db
from . import address_book as db_rubrica
from . import inventory as db_magazzino # Needed for stock updates

# --- Constants ---
PDF_EXPORT_DIR = "DOCUMENTI_PDF" # Will be created in the root folder
VALID_INVOICE_STATUS = ["In sospeso", "Pagato", "Scaduto", "Annullato"]
VALID_QUOTE_STATUS = ["Bozza", "Inviato", "Accettato", "Rifiutato", "Fatturato"]

# Setup Jinja2 environment to load the HTML template
try:
    # Load templates from the root directory (where frontend_gui.py is)
    env = Environment(
        loader=FileSystemLoader('.'), 
        autoescape=select_autoescape(['html', 'xml'])
    )
    # Add a custom filter to Jinja2 to replace newlines with <br> tags
    env.filters['nl2br'] = lambda s: str(s).replace('\n', '<br>\n')
except Exception as e:
    print(f"CRITICAL ERROR: Could not initialize Jinja2 environment: {e}")

# --- Data Persistence ---

def find_document_by_id(doc_id):
    """
    Finds a single document (quote or invoice) by its ID.

    Args:
        doc_id (str): The 'id' of the document to find.

    Returns:
        dict: The document dictionary if found, else None.
    """
    documents = db.load_data(db.DOCUMENTI_DB)
    for doc in documents:
        if doc.get('id') == doc_id:
            return doc
    return None

def get_all_documents(doc_type=None):
    """
    Gets all documents, optionally filtering by type ('quote' or 'invoice').

    Args:
        doc_type (str, optional): 'quote' or 'invoice'.

    Returns:
        list: A list of document dictionaries.
    """
    documents = db.load_data(db.DOCUMENTI_DB)
    if doc_type:
        return [d for d in documents if d.get('doc_type') == doc_type]
    return documents

# --- Core Logic: Calculations ---

def _calculate_totals(items, discount_perc=Decimal('0'), vat_perc=Decimal('22'), ritenuta_perc=Decimal('0')):
    """
    Performs financial calculations using Decimal for precision.
    Includes subtotal, discount, taxable amount, VAT, withholding tax (ritenuta),
    and final amount due.

    Args:
        items (list): List of item dicts. Each must have 'qty' and 'unit_price'.
        discount_perc (Decimal): Discount percentage (e.g., Decimal('10')).
        vat_perc (Decimal): VAT percentage (e.g., Decimal('22')).
        ritenuta_perc (Decimal): Withholding tax percentage (e.g., Decimal('20')).

    Returns:
        dict: A dictionary containing all calculated financial fields
              (subtotal, discount_amount, taxable_amount, vat_amount,
               ritenuta_amount, total, total_da_pagare).
    """
    # Ensure all inputs are Decimal for precision
    discount_perc = Decimal(str(discount_perc))
    vat_perc = Decimal(str(vat_perc))
    ritenuta_perc = Decimal(str(ritenuta_perc))
    
    subtotal = Decimal('0')
    
    # Calculate subtotal from line items
    for item in items:
        qty = Decimal(str(item.get('qty', '1')))
        unit_price = Decimal(str(item.get('unit_price', '0')))
        item_total = qty * unit_price
        item['total'] = item_total # Store line total in the item dict
        subtotal += item_total
        
    # Calculate discount
    discount_amount = (subtotal * (discount_perc / Decimal('100'))).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )
    
    taxable_amount = subtotal - discount_amount
    
    # Calculate VAT (IVA)
    vat_amount = (taxable_amount * (vat_perc / Decimal('100'))).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )
    
    # This is the gross total of the document
    total = taxable_amount + vat_amount
    
    # Calculate withholding tax (Ritenuta) on the taxable amount
    ritenuta_amount = (taxable_amount * (ritenuta_perc / Decimal('100'))).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )
    
    # This is the final net amount the client has to pay
    total_da_pagare = total - ritenuta_amount
    
    return {
        'subtotal': subtotal,
        'discount_perc': discount_perc,
        'discount_amount': discount_amount,
        'taxable_amount': taxable_amount,
        'vat_perc': vat_perc,
        'vat_amount': vat_amount,
        'total': total, # Gross document total
        'ritenuta_perc': ritenuta_perc,
        'ritenuta_amount': ritenuta_amount,
        'total_da_pagare': total_da_pagare, # Net amount to be paid
        'items': items # Return items with calculated 'total'
    }

# --- Core Logic: Quotes ---

def create_quote(client_id, project_id, items, discount_perc, vat_perc, notes=""):
    """
    Creates a new quote document and saves it.
    Ritenuta (withholding tax) is assumed to be 0 for quotes.

    Args:
        client_id (str): The associated client ID from the address book.
        project_id (str): The associated project ID (optional).
        items (list): List of line item dicts.
        discount_perc (Decimal): Discount percentage.
        vat_perc (Decimal): VAT percentage.
        notes (str): Footer notes for the document.

    Returns:
        dict: The newly created quote.
    Raises:
        ValueError: If the client_id is not found or numbers are invalid.
    """
    if not db_rubrica.find_contact_by_id(client_id):
        raise ValueError("Client ID not found.")

    try:
        # Ritenuta is always 0 for quotes
        calculations = _calculate_totals(items, discount_perc, vat_perc, Decimal('0'))
    except InvalidOperation as e:
        raise ValueError(f"Invalid number in line items: {e}")
    
    quote = {
        'id': str(uuid.uuid4()),
        'doc_type': 'quote',
        'number': db.get_next_document_number('quote'),
        'date': date.today().isoformat(),
        'client_id': client_id,
        'project_id': project_id,
        'status': 'Bozza', # Default status
        'notes': notes,
    }
    
    quote.update(calculations) # Add all calculated fields
    
    documents = db.load_data(db.DOCUMENTI_DB)
    documents.append(quote)
    db.save_data(db.DOCUMENTI_DB, documents)
    
    return quote

# --- Core Logic: Invoices ---

def create_invoice(client_id, project_id, items, discount_perc, vat_perc, ritenuta_perc, due_date, notes=""):
    """
    Creates a new invoice document and saves it.
    This function *also* updates warehouse stock if items are linked.

    Args:
        client_id (str): The associated client ID.
        project_id (str): The associated project ID (optional).
        items (list): List of line item dicts. Can contain 'articolo_id'.
        discount_perc (Decimal): Discount percentage.
        vat_perc (Decimal): VAT percentage.
        ritenuta_perc (Decimal): Withholding tax percentage.
        due_date (str): Due date in 'YYYY-MM-DD' format.
        notes (str): Footer notes.

    Returns:
        dict: The newly created invoice.
    Raises:
        ValueError: If client_id is not found or stock update fails.
    """
    if not db_rubrica.find_contact_by_id(client_id):
        raise ValueError("Client ID not found.")

    # Perform calculations first
    try:
        calculations = _calculate_totals(items, discount_perc, vat_perc, ritenuta_perc)
    except InvalidOperation as e:
        raise ValueError(f"Invalid number in line items: {e}")

    invoice = {
        'id': str(uuid.uuid4()),
        'doc_type': 'invoice',
        'number': db.get_next_document_number('invoice'),
        'date': date.today().isoformat(),
        'due_date': due_date,
        'client_id': client_id,
        'project_id': project_id,
        'status': 'In sospeso', # Default status
        'notes': notes,
    }
    
    invoice.update(calculations) # Add calculated fields
    
    # --- Warehouse Stock Update ---
    # After creating the invoice, decrease stock for linked items
    stock_errors = []
    for item in invoice['items']:
        # 'articolo_id' is the new key, 'linked_item_id' is legacy
        item_id = item.get('articolo_id') or item.get('linked_item_id') 
        if item_id:
            try:
                qta_to_remove = Decimal(str(item.get('qty', '0'))) * -1 # Make it negative
                if qta_to_remove != 0:
                    success, msg = db_magazzino.update_stock(item_id, qta_to_remove)
                    if not success:
                        stock_errors.append(f"Item '{item['description']}': {msg}")
            except Exception as e:
                stock_errors.append(f"Item '{item['description']}': Error {e}")
    
    if stock_errors:
        # If stock update fails, stop and report the error.
        # The invoice is *not* saved.
        raise ValueError("Stock update failed: " + ", ".join(stock_errors))
    
    # All good, save the invoice
    documents = db.load_data(db.DOCUMENTI_DB)
    documents.append(invoice)
    db.save_data(db.DOCUMENTI_DB, documents)
    
    return invoice

def convert_quote_to_invoice(quote_id, due_date, ritenuta_perc):
    """
    Finds a quote and generates a new invoice from it.
    This also updates warehouse stock.

    Args:
        quote_id (str): The 'id' of the quote to convert.
        due_date (str): The due date for the new invoice.
        ritenuta_perc (Decimal): The withholding tax for the new invoice.

    Returns:
        tuple (bool, dict or str): (True, new_invoice_dict) on success,
                                   (False, "Error message") on failure.
    """
    quote = find_document_by_id(quote_id)
    if not quote or quote['doc_type'] != 'quote':
        return False, "Preventivo non trovato."
    if quote['status'] == 'Fatturato':
        return False, "Preventivo già fatturato."

    try:
        # Create the invoice. This will also handle stock reduction.
        new_invoice = create_invoice(
            client_id=quote['client_id'],
            project_id=quote.get('project_id'),
            items=quote['items'],
            discount_perc=quote['discount_perc'],
            vat_perc=quote['vat_perc'],
            ritenuta_perc=ritenuta_perc, # Pass the new Ritenuta
            due_date=due_date,
            notes=quote.get('notes', '')
        )
    except Exception as e:
        return False, f"Errore creazione fattura: {e}"
    
    # If invoice creation succeeds, update the quote status
    quote['status'] = 'Fatturato'
    update_document(quote_id, quote) # This saves the change
    
    return True, new_invoice

def update_document_status(doc_id, new_status):
    """
    Updates the 'status' field of an existing document.

    Args:
        doc_id (str): The 'id' of the document to update.
        new_status (str): The new status (must be valid).

    Returns:
        tuple (bool, dict or str): (True, updated_document) on success,
                                   (False, "Error message") on failure.
    Raises:
        ValueError: If the new status is not in the valid lists.
    """
    documents = db.load_data(db.DOCUMENTI_DB)
    doc_found = False
    
    for i, doc in enumerate(documents):
        if doc['id'] == doc_id:
            # Validate status based on document type
            if doc['doc_type'] == 'invoice' and new_status not in VALID_INVOICE_STATUS:
                raise ValueError(f"Stato fattura non valido: {new_status}")
            if doc['doc_type'] == 'quote' and new_status not in VALID_QUOTE_STATUS:
                raise ValueError(f"Stato preventivo non valido: {new_status}")

            documents[i]['status'] = new_status
            doc_found = True
            break
            
    if doc_found:
        db.save_data(db.DOCUMENTI_DB, documents)
        return True, documents[i]
    
    return False, "Documento non trovato."

def update_document(doc_id, updated_data):
    """
    Generic function to update a document (used internally by convert_quote).
    This function is less safe than specific updaters.

    Args:
        doc_id (str): The 'id' of the document to update.
        updated_data (dict): Dictionary of data to merge.

    Returns:
        bool: True on success, False if not found.
    """
    documents = db.load_data(db.DOCUMENTI_DB)
    doc_found = False
    for i, doc in enumerate(documents):
        if doc['id'] == doc_id:
            doc.update(updated_data)
            documents[i] = doc
            doc_found = True
            break
    if doc_found:
        db.save_data(db.DOCUMENTI_DB, documents)
        return True
    return False

# --- Exporting: PDF ---

def export_to_pdf(doc_id):
    """
    Generates a PDF representation of the document using WeasyPrint
    and an HTML template.

    Args:
        doc_id (str): The 'id' of the document to export.

    Returns:
        tuple (bool, str): (True, "Path to PDF") on success,
                           (False, "Error message") on failure.
    """
    doc = find_document_by_id(doc_id)
    if not doc:
        return False, "Documento non trovato."

    # Get client data
    client = db_rubrica.find_contact_by_id(doc['client_id'])
    if not client:
        return False, "Cliente associato non trovato."

    # Get my company details from settings
    settings = db.load_settings()
    my_details_str = settings.get('my_company_details', "My Company\nMy Address")
    
    # Parse my_company_details for the template
    # Assumes format: Name\nAddress\nP.IVA: 123
    try:
        my_details_parts = my_details_str.split('\n')
        my_details_data = {
            'name': my_details_parts[0],
            'address': "\n".join(my_details_parts[1:-1]),
            'vat_id': my_details_parts[-1].replace("P.IVA: ", "")
        }
    except IndexError:
        # Fallback if the format is wrong
        my_details_data = {
            'name': 'Dati Azienda Non Configurati',
            'address': 'Controlla i settings',
            'vat_id': 'N/D'
        }

    # Setup PDF path
    os.makedirs(PDF_EXPORT_DIR, exist_ok=True)
    filename = f"{doc['number'].replace('/', '-')}_{doc['doc_type']}.pdf"
    filepath = os.path.join(PDF_EXPORT_DIR, filename)
    
    try:
        # Load the HTML template file
        template = env.get_template('invoice_template.html')
        
        # Add a display-friendly type to the doc
        doc['doc_type_display'] = "FATTURA" if doc['doc_type'] == 'invoice' else "PREVENTIVO"
        
        # Render the template with all the data
        html_out = template.render(
            doc=doc,
            client=client,
            my_details=my_details_data
        )
        
        # Use WeasyPrint to generate the PDF from the rendered HTML
        HTML(string=html_out).write_pdf(filepath)
        
        return True, filepath
    
    except Exception as e:
        return False, f"Errore generazione PDF: {e}"

# --- Analysis: Statistics ---

def get_annual_stats(year):
    """
    Generates annual statistics based on *paid* invoices.

    Args:
        year (int): The year to analyze.

    Returns:
        tuple (dict, str): (stats_dict, "Success/Error message").
                           Stats dict contains 'total_revenue' and 'top_clients' (DataFrame).
                           Returns (None, "Error message") on failure.
    """
    try:
        year = int(year)
    except ValueError:
        return None, "Anno non valido."

    invoices = get_all_documents(doc_type='invoice')
    
    # Filter for paid invoices in the specified year
    paid_invoices = []
    for inv in invoices:
        if inv['status'] != 'Pagato':
            continue
        try:
            invoice_year = datetime.strptime(inv['date'], '%Y-%m-%d').year
            if invoice_year == year:
                paid_invoices.append(inv)
        except ValueError:
            continue
            
    if not paid_invoices:
        return {'total_revenue': 0, 'top_clients': pd.DataFrame()}, "Nessuna fattura pagata trovata per l'anno."

    # Use Pandas for easy aggregation
    df = pd.DataFrame(paid_invoices)
    
    # Convert Decimal to float for pandas operations
    # Revenue is based on the net amount paid by the client
    df['total_numeric'] = df['total_da_pagare'].apply(lambda x: float(x))
    
    # 1. Total Revenue (based on 'total_da_pagare')
    total_revenue = df['total_numeric'].sum()
    
    # 2. Top Clients
    # Create a map of client IDs to names
    client_names = {c['id']: c.get('name', 'N/A') for c in db_rubrica.get_all_contacts()}
    df['client_name'] = df['client_id'].map(client_names)
    
    # Group by client name and sum their paid totals
    top_clients = df.groupby('client_name')['total_numeric'].sum().sort_values(ascending=False).reset_index()
    top_clients.columns = ['Cliente', 'Fatturato']
    
    stats = {
        'total_revenue': total_revenue,
        'top_clients': top_clients
    }
    
    return stats, "Statistiche generate."