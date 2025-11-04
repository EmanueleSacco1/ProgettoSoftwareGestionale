import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Import backend modules using relative imports
from . import projects as db_progetti
from . import address_book as db_rubrica # Needed to get client names

def _get_all_attivita_df():
    """
    Helper function to load all activities from all projects into a single DataFrame.
    This is the base for all reporting functions.
    It enriches the activity data with project and client names.
    
    Returns:
        pd.DataFrame: A DataFrame containing all time-tracking entries,
                      or an empty DataFrame if none exist.
    """
    projects = db_progetti.get_all_projects()
    all_activities = []
    
    # Load client names once for efficiency
    client_names = {c['id']: c.get('name', 'N/A') for c in db_rubrica.get_all_contacts()}
    
    for project in projects:
        project_name = project.get('name', 'Senza Nome')
        client_id = project.get('client_id')
        client_name = client_names.get(client_id, 'N/A')
        
        for att in project.get('attivita', []):
            # Create a copy and add project context
            new_att = att.copy()
            new_att['project_id'] = project['id']
            new_att['project_name'] = project_name
            new_att['client_name'] = client_name
            
            # --- BACKWARDS COMPATIBILITY ---
            # If 'fatturabile' key doesn't exist (for old data),
            # default it to True.
            if 'fatturabile' not in new_att:
                new_att['fatturabile'] = True
            
            all_activities.append(new_att)
            
    if not all_activities:
        return pd.DataFrame()
        
    # Convert to DataFrame
    df = pd.DataFrame(all_activities)
    
    # Convert types for analysis
    df['ore'] = pd.to_numeric(df['ore'])
    df['data'] = pd.to_datetime(df['data'])
    
    return df

def generate_report_ore(start_date, end_date):
    """
    Generates a simple report of billable vs. non-billable hours
    in a given date range.

    Args:
        start_date (datetime): The start of the period.
        end_date (datetime): The end of the period.

    Returns:
        tuple (dict, str): (report_dict, "Success/Error message").
                           Returns (None, "Error message") on failure.
    """
    df = _get_all_attivita_df()
    if df.empty:
        return None, "Nessuna attività registrata."
        
    # Filter by date range
    mask = (df['data'] >= start_date) & (df['data'] <= end_date)
    df_periodo = df.loc[mask]
    
    if df_periodo.empty:
        return None, "Nessuna attività nel periodo selezionato."
        
    # Group by 'fatturabile' (billable) status and sum 'ore'
    report = df_periodo.groupby('fatturabile')['ore'].sum()
    
    report_dict = {
        'fatturabili': report.get(True, 0.0),
        'non_fatturabili': report.get(False, 0.0)
    }
    
    report_dict['totali'] = report_dict['fatturabili'] + report_dict['non_fatturabili']
    
    return report_dict, "Report generato."

def generate_analisi_progetti_onerose(start_date, end_date):
    """
    Analyzes which projects and clients consumed the most hours in a period.
    This fulfills "analisi delle attività più onerose".

    Args:
        start_date (datetime): The start of the period.
        end_date (datetime): The end of the period.

    Returns:
        tuple (pd.Series, pd.Series, str):
            - (Series of hours grouped by project,
            -  Series of hours grouped by client,
            -  "Success/Error message")
            Returns (None, None, "Error message") on failure.
    """
    df = _get_all_attivita_df()
    if df.empty:
        return None, None, "Nessuna attività registrata."
        
    # Filter by date range
    mask = (df['data'] >= start_date) & (df['data'] <= end_date)
    df_periodo = df.loc[mask]
    
    if df_periodo.empty:
        return None, None, "Nessuna attività nel periodo selezionato."
        
    # Group by project name and sum hours, sort descending
    report_progetti = df_periodo.groupby('project_name')['ore'].sum().sort_values(ascending=False)
    
    # Also group by client
    report_clienti = df_periodo.groupby('client_name')['ore'].sum().sort_values(ascending=False)
    
    return report_progetti, report_clienti, "Analisi generata."

def plot_produttivita_mensile(year, filename="produttivita_mensile.png"):
    """
    Generates a stacked bar chart of monthly productivity (billable vs. non-billable).
    
    Args:
        year (int): The year to analyze.
        filename (str): The path to save the .png file.
        
    Returns:
        tuple (bool, str): (True, "Success message") or (False, "Error message").
    """
    df = _get_all_attivita_df()
    if df.empty:
        return False, "Nessuna attività registrata."
        
    # Filter by year and set the date as the index for resampling
    df_year = df[df['data'].dt.year == year].copy()
    if df_year.empty:
        return False, f"Nessuna attività trovata per l'anno {year}."
    df_year.set_index('data', inplace=True)
    
    # Group by month (using 'ME' for Month End) and 'fatturabile' status, then sum 'ore'.
    # .unstack() pivots 'fatturabile' (True/False) to become columns.
    stats_df = df_year.groupby(
        [pd.Grouper(freq='ME'), 'fatturabile']
    )['ore'].sum().unstack(fill_value=0)

    # Rename columns for a cleaner legend in the plot
    stats_df.rename(columns={True: 'Fatturabili', False: 'Non Fatturabili'}, inplace=True)
    
    # Format index to 'YYYY-MM' for readability
    stats_df.index = stats_df.index.strftime('%Y-%m')
    
    if stats_df.empty:
        return False, "Nessun dato da plottare per l'anno."

    # Create the stacked bar chart
    ax = stats_df.plot(
        kind='bar', 
        stacked=True, 
        figsize=(12, 7), 
        rot=45,
        title=f"Produttività Mensile (Ore) - Anno {year}"
    )

    ax.set_ylabel("Ore Totali")
    ax.set_xlabel("Mese")
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save the figure to a file
    try:
        plt.tight_layout()
        plt.savefig(filename)
        plt.close() # Close the plot to free memory
        return True, f"Grafico salvato come {filename}"
    except Exception as e:
        return False, f"Errore salvataggio grafico: {e}"