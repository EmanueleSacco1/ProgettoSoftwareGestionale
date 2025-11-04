import os
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd

# Import all backend modules to read data, using relative imports
from . import persistence as db
from . import address_book as db_rubrica
from . import projects as db_progetti
from . import documents as db_docs
from . import calendar as db_calendario
from . import ledger as db_ledger
from . import time_reports as db_reporting

# Import PDF generation tools from reportlab
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm

# --- Dashboard UI Functions ---

def get_dati_cruscotto():
    """
    Fetches all data points required for the main dashboard UI.
    This function reads from multiple backend modules to create a summary.

    Returns:
        dict: A dictionary containing all summary points for the dashboard.
    """
    today = datetime.now().date()
    current_year = today.year
    
    # 1. Active Projects
    progetti_attivi = db_progetti.get_all_projects(status_filter="In corso")
    
    # 2. Unpaid Invoices
    fatture = db_docs.get_all_documents(doc_type='invoice')
    fatture_da_incassare = []
    totale_da_incassare = Decimal('0')
    for f in fatture:
        if f.get('status') in ['In sospeso', 'Scaduto']:
            fatture_da_incassare.append(f)
            # Use 'total_da_pagare' which includes Ritenuta
            totale_da_incassare += f.get('total_da_pagare', Decimal('0'))
            
    # 3. Upcoming Deadlines (Next 7 days)
    end_date = today + timedelta(days=7)
    scadenze_imminenti = db_calendario.get_eventi(today, end_date)
    
    # 4. Earning Statistics (Cash basis, Year-To-Date)
    # We use the internal _get_dataframe helper from the ledger
    df_movimenti, _ = db_ledger._get_dataframe(current_year)
    incassato_ytd = Decimal('0')
    uscite_ytd = Decimal('0')
    if not df_movimenti.empty:
        # Sum 'amount_totale' from the financial ledger
        incassato_ytd = Decimal(str(
            df_movimenti[df_movimenti['type'] == 'Entrata']['amount_totale'].sum()
        ))
        uscite_ytd = Decimal(str(
            df_movimenti[df_movimenti['type'] == 'Uscita']['amount_totale'].sum()
        ))

    # Assemble the final dictionary
    return {
        'progetti_attivi_count': len(progetti_attivi),
        'progetti_attivi_list': progetti_attivi[:5], # Show only the first 5
        'fatture_da_incassare_count': len(fatture_da_incassare),
        'fatture_da_incassare_totale': totale_da_incassare,
        'scadenze_imminenti_list': scadenze_imminenti,
        'incassato_ytd': incassato_ytd,
        'uscite_ytd': uscite_ytd,
        'margine_ytd': incassato_ytd - uscite_ytd
    }

# --- Comprehensive Annual Report Functions ---

def _get_report_dataframes(year):
    """
    Helper function to get all data for the annual report as Pandas DataFrames.

    Args:
        year (int): The year to report on.

    Returns:
        dict: A dictionary of DataFrames {'fatture', 'movimenti', 'ore'}.
    """
    # 1. Invoice Data
    fatture_anno = []
    client_names = {c['id']: c.get('name', 'N/A') for c in db_rubrica.get_all_contacts()}
    
    for doc in db_docs.get_all_documents(doc_type='invoice'):
        try:
            if datetime.strptime(doc['date'], '%Y-%m-%d').year == year:
                doc['client_name'] = client_names.get(doc['client_id'], 'N/A')
                fatture_anno.append(doc)
        except ValueError:
            continue
            
    df_fatture = pd.DataFrame(fatture_anno)
    if not df_fatture.empty:
        # Select and rename columns for the report
        df_fatture = df_fatture[[
            'date', 'number', 'client_name', 'status', 'taxable_amount', 
            'vat_amount', 'ritenuta_amount', 'total_da_pagare'
        ]].rename(columns={
            'date': 'Data', 'number': 'Numero', 'client_name': 'Cliente',
            'status': 'Stato', 'taxable_amount': 'Imponibile', 
            'vat_amount': 'IVA', 'ritenuta_amount': 'Ritenuta',
            'total_da_pagare': 'Netto a Pagare'
        })
        # Convert Decimal to float for Pandas
        for col in ['Imponibile', 'IVA', 'Ritenuta', 'Netto a Pagare']:
            df_fatture[col] = df_fatture[col].astype(float)

    # 2. Financial Ledger (Prima Nota) Data
    df_movimenti, _ = db_ledger._get_dataframe(year) # This helper already returns a DF
    if not df_movimenti.empty:
        df_movimenti = df_movimenti.reset_index()[[
            'date', 'type', 'description', 'amount_netto', 'amount_iva', 
            'amount_ritenuta', 'amount_totale'
        ]].rename(columns={
            'date': 'Data', 'type': 'Tipo', 'description': 'Descrizione',
            'amount_netto': 'Imponibile', 'amount_iva': 'IVA',
            'amount_ritenuta': 'Ritenuta', 'amount_totale': 'Totale'
        })

    # 3. Time Tracking Data
    df_ore = db_reporting._get_all_attivita_df() # This helper returns a full DF
    if not df_ore.empty:
        df_ore = df_ore[df_ore['data'].dt.year == year] # Filter by year
        df_ore = df_ore[[
            'data', 'project_name', 'client_name', 'ore', 'fatturabile', 'descrizione'
        ]].rename(columns={
            'data': 'Data', 'project_name': 'Progetto', 'client_name': 'Cliente',
            'ore': 'Ore', 'fatturabile': 'Fatturabile', 'descrizione': 'Descrizione'
        })
    
    return {
        'fatture': df_fatture,
        'movimenti': df_movimenti,
        'ore': df_ore
    }

def _export_to_excel(dataframes, filename):
    """
    Exports multiple DataFrames to a single Excel file with multiple sheets.

    Args:
        dataframes (dict): The dict of DataFrames from _get_report_dataframes.
        filename (str): The target .xlsx file name.

    Returns:
        tuple (bool, str): (True, "Success message") or (False, "Error message").
    """
    try:
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            if 'fatture' in dataframes and not dataframes['fatture'].empty:
                dataframes['fatture'].to_excel(writer, sheet_name='Riepilogo Fatture', index=False)
            if 'movimenti' in dataframes and not dataframes['movimenti'].empty:
                dataframes['movimenti'].to_excel(writer, sheet_name='Riepilogo PrimaNota', index=False)
            if 'ore' in dataframes and not dataframes['ore'].empty:
                dataframes['ore'].to_excel(writer, sheet_name='Dettaglio Ore', index=False)
        return True, f"Report Excel salvato come {filename}"
    except Exception as e:
        return False, f"Errore durante l'esportazione Excel: {e}"

def _export_to_pdf(dataframes, filename, year):
    """
    Exports data to a multi-page PDF using ReportLab Platypus tables.
    This is a simple, non-template-based PDF for raw data.

    Args:
        dataframes (dict): The dict of DataFrames from _get_report_dataframes.
        filename (str): The target .pdf file name.
        year (int): The year for the report title.

    Returns:
        tuple (bool, str): (True, "Success message") or (False, "Error message").
    """
    try:
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        story = [] # A list of ReportLab 'Flowables'
        styles = getSampleStyleSheet()
        
        story.append(Paragraph(f"Report Annuale {year}", styles['h1']))
        story.append(Spacer(1, 1*cm))

        # Define a generic table style
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])

        # Table 1: Invoices
        if 'fatture' in dataframes and not dataframes['fatture'].empty:
            story.append(Paragraph("Riepilogo Fatture Emesse", styles['h2']))
            df = dataframes['fatture'].head(50) # Limit to 50 rows for PDF
            data = [df.columns.values.tolist()] + df.values.tolist()
            t = Table(data, colWidths=[2.5*cm, 2.5*cm, 3*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2.5*cm])
            t.setStyle(table_style)
            story.append(t)
            story.append(Spacer(1, 1*cm))

        # Table 2: Financial Ledger
        if 'movimenti' in dataframes and not dataframes['movimenti'].empty:
            story.append(Paragraph("Riepilogo Movimenti Prima Nota", styles['h2']))
            df = dataframes['movimenti'].head(50) # Limit to 50 rows
            data = [df.columns.values.tolist()] + df.values.tolist()
            t = Table(data, colWidths=[2.5*cm, 1.5*cm, 5*cm, 2*cm, 2*cm, 2*cm, 2.5*cm])
            t.setStyle(table_style)
            story.append(t)
            story.append(Spacer(1, 1*cm))

        # Table 3: Time Tracking
        if 'ore' in dataframes and not dataframes['ore'].empty:
            story.append(Paragraph("Riepilogo Ore Lavorate", styles['h2']))
            df = dataframes['ore'].head(50) # Limit to 50 rows
            data = [df.columns.values.tolist()] + df.values.tolist()
            t = Table(data, colWidths=[2.5*cm, 3*cm, 3*cm, 1.5*cm, 2*cm, 6.5*cm])
            t.setStyle(table_style)
            story.append(t)
            story.append(Spacer(1, 1*cm))

        if len(story) <= 2: # Only titles were added
            return False, "Nessun dato trovato per il PDF."

        doc.build(story)
        return True, f"Report PDF salvato come {filename}"
    except Exception as e:
        return False, f"Errore during l'esportazione PDF: {e}"

def export_report_completo(year, format='excel'):
    """
    Main export function. Fetches all data and calls the
    correct exporter (Excel or PDF).

    Args:
        year (int): The year to report on.
        format (str): 'excel' or 'pdf'.

    Returns:
        tuple (bool, str): (True, "Success message") or (False, "Error message").
    """
    print(f"Recupero dati per l'anno {year}...")
    dataframes = _get_report_dataframes(year)
    
    if (dataframes['fatture'].empty and 
        dataframes['movimenti'].empty and 
        dataframes['ore'].empty):
        return False, f"Nessun dato trovato per l'anno {year}."
        
    if format == 'excel':
        filename = f"report_annuale_{year}.xlsx"
        return _export_to_excel(dataframes, filename)
    elif format == 'pdf':
        filename = f"report_annuale_{year}.pdf"
        return _export_to_pdf(dataframes, filename, year)
    else:
        return False, "Formato non valido."