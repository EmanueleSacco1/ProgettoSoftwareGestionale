from decimal import Decimal, InvalidOperation
from datetime import datetime

# Import centralized modules using relative imports
from . import persistence as db
from . import documents as db_docs
from . import ledger as db_ledger

# --- Private Calculation Helpers ---

def _get_dates_for_quarter(year, quarter):
    """
    Helper to get start and end date objects for a given quarter.

    Args:
        year (int): The calendar year.
        quarter (int): The quarter (1-4).

    Returns:
        tuple (datetime.date, datetime.date): (start_date, end_date)
    
    Raises:
        ValueError: If the quarter is not between 1 and 4.
    """
    if quarter == 1:
        start_date = datetime(year, 1, 1).date()
        end_date = datetime(year, 3, 31).date()
    elif quarter == 2:
        start_date = datetime(year, 4, 1).date()
        end_date = datetime(year, 6, 30).date()
    elif quarter == 3:
        start_date = datetime(year, 7, 1).date()
        end_date = datetime(year, 9, 30).date()
    elif quarter == 4:
        start_date = datetime(year, 10, 1).date()
        end_date = datetime(year, 12, 31).date()
    else:
        raise ValueError("Invalid quarter. Use 1-4.")
    return start_date, end_date

def _get_dati_iva(start_date, end_date):
    """
    Calculates VAT (IVA) totals for a given period.
    - VAT Debit (from issued invoices)
    - VAT Credit (from expenses in the ledger)

    Args:
        start_date (datetime.date): The start of the period.
        end_date (datetime.date): The end of the period.

    Returns:
        dict: A dictionary with 'iva_debito', 'iva_credito', 'iva_da_versare'.
    """
    iva_debito = Decimal('0')
    iva_credito = Decimal('0')
    
    # 1. VAT Debit (from Invoices issued in the period)
    all_invoices = db_docs.get_all_documents(doc_type='invoice')
    for inv in all_invoices:
        try:
            inv_date = datetime.strptime(inv['date'], '%Y-%m-%d').date()
            if start_date <= inv_date <= end_date:
                iva_debito += inv.get('vat_amount', Decimal('0'))
        except ValueError:
            continue
            
    # 2. VAT Credit (from 'Uscita' entries in Prima Nota in the period)
    all_movimenti = db_ledger._get_movimenti()
    for mov in all_movimenti:
        if mov.get('type') == 'Uscita': # Only expenses
            try:
                mov_date = datetime.strptime(mov['date'], '%Y-%m-%d').date()
                if start_date <= mov_date <= end_date:
                    iva_credito += mov.get('amount_iva', Decimal('0'))
            except ValueError:
                continue
                
    # Calculate the net VAT to be paid
    iva_da_versare = iva_debito - iva_credito
    
    return {
        'iva_debito': iva_debito,
        'iva_credito': iva_credito,
        'iva_da_versare': iva_da_versare
    }

def _get_dati_contributivi(year, tax_config):
    """
    Calculates INPS and IRPEF estimates based on cash received (Regime di Cassa).
    This provides a Year-To-Date (YTD) projection.

    Args:
        year (int): The year to analyze.
        tax_config (dict): Contains 'inps_perc' and 'irpef_perc'.

    Returns:
        dict: A dictionary with 'imponibile_cassa', 'contributi_inps',
              'imponibile_irpef', 'stima_irpef'.
    """
    try:
        inps_perc = Decimal(str(tax_config.get('inps_perc', '0'))) / 100
        irpef_perc = Decimal(str(tax_config.get('irpef_perc', '0'))) / 100
    except InvalidOperation:
        raise ValueError("Invalid tax rates in settings.")

    # Load the financial ledger (Prima Nota) for the year
    df_movimenti, msg = db_ledger._get_dataframe(year)
    
    if df_movimenti.empty:
        return {
            'imponibile_cassa': Decimal('0'),
            'contributi_inps': Decimal('0'),
            'imponibile_irpef': Decimal('0'),
            'stima_irpef': Decimal('0')
        }
        
    # Calculate Taxable Income (Cash basis): Sum of 'amount_netto' from 'Entrata'
    imponibile_cassa = Decimal(str(
        df_movimenti[df_movimenti['type'] == 'Entrata']['amount_netto'].sum()
    ))
    
    # Calculate estimated INPS contributions
    contributi_inps = imponibile_cassa * inps_perc
    
    # Calculate IRPEF
    # IRPEF Taxable Income = Cash Income - INPS contributions
    imponibile_irpef = imponibile_cassa - contributi_inps
    if imponibile_irpef < 0:
        imponibile_irpef = Decimal('0')
        
    stima_irpef = imponibile_irpef * irpef_perc
    
    return {
        'imponibile_cassa': imponibile_cassa,
        'contributi_inps': contributi_inps,
        'imponibile_irpef': imponibile_irpef,
        'stima_irpef': stima_irpef
    }

# --- Public Functions ---

def get_stima_completa(year, quarter):
    """
    Main function called by the frontend.
    Generates VAT estimates for the specified quarter and
    INPS/IRPEF estimates for the full year (Year-To-Date).

    Args:
        year (int): The year to analyze.
        quarter (int): The quarter (1-4) for VAT calculation.

    Returns:
        tuple (dict, str): (results_dict, "Success message") or (None, "Error message").
    """
    try:
        # Load tax configuration from settings
        settings = db.load_settings()
        tax_config = settings.get('tax_config', {})
        
        # 1. Calculate Quarterly VAT
        start_q, end_q = _get_dates_for_quarter(year, quarter)
        dati_iva = _get_dati_iva(start_q, end_q)
        
        # 2. Calculate YTD INPS/IRPEF (based on cash received)
        dati_contributivi = _get_dati_contributivi(year, tax_config)
        
        # Merge the results
        risultato = {}
        risultato.update(dati_iva)
        risultato.update(dati_contributivi)
        risultato['tax_config'] = tax_config
        risultato['periodo'] = f"Q{quarter} {year}"
        
        return risultato, "Estimate generated."
        
    except Exception as e:
        return None, f"Error during estimate generation: {e}"