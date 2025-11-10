import pickle
import os
from datetime import datetime

# --- Constants: File Paths ---
# Define filenames for all data persistence files.
# These will be created in the root folder.
RUBRICA_DB = 'rubrica.pkl'
PROGETTI_DB = 'progetti.pkl'
DOCUMENTI_DB = 'documenti.pkl'
CALENDARIO_DB = 'calendario.pkl'
MAGAZZINO_DB = 'magazzino.pkl'
PRIMANOTA_DB = 'primanota.pkl'
SETTINGS_FILE = 'settings.pkl'

# --- Generic Data Persistence ---

def load_data(db_name):
    """
    Loads a data list from a specified pickle file.
    
    Args:
        db_name (str): The filename constant (e.g., RUBRICA_DB) to load from.

    Returns:
        list: The loaded list of data, or an empty list if the file
              doesn't exist or is empty/corrupt.
    """
    if os.path.exists(db_name):
        try:
            # Open in read-binary mode
            with open(db_name, 'rb') as f:
                return pickle.load(f)
        except (EOFError, pickle.UnpicklingError):
            # File is empty or corrupt, return empty list
            return []
    return []

def save_data(db_name, data):
    """
    Saves an entire data list to a specified pickle file.
    
    Args:
        db_name (str): The filename constant (e.g., RUBRICA_DB) to save to.
        data (list): The list of data to save.
    """
    # Open in write-binary mode
    with open(db_name, 'wb') as f:
        pickle.dump(data, f)

# --- Application Settings Management ---

def load_settings():
    """
    Loads application settings (e.g., counters, API keys, user prefs).
    
    This function merges saved settings with defaults to ensure that
    new settings (added during development) are present in the application.

    Returns:
        dict: The complete settings dictionary.
    """
    # Define default structure for all application settings
    defaults = {
        'last_invoice_num': 0,
        'last_quote_num': 0,
        'invoice_prefix': f"F{datetime.now().year}/",
        'quote_prefix': f"P{datetime.now().year}/",
        'my_company_details': "Your Name / Your Company\nStreet, City, ZIP\nVAT ID: 0123456789",
        'smtp_config': {
            'host': '',
            'port': 587,
            'user': '',
            'password': '',
            'notify_email': '' # Email to send notifications to
        },
        'tax_config': {
            'inps_perc': 26.07,
            'irpef_perc': 23.0
        }
    }
    
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'rb') as f:
                settings = pickle.load(f)
                
                # Merge defaults with loaded settings to ensure all keys exist
                # This is crucial for adding new features without breaking old installs
                for key, value in defaults.items():
                    if key not in settings:
                        # If a top-level key is missing, add it
                        settings[key] = value
                    elif isinstance(value, dict):
                         # If the key is a dict, check for missing sub-keys
                         for sub_key, sub_value in value.items():
                            if key not in settings or sub_key not in settings[key]:
                                if key not in settings:
                                    settings[key] = {}
                                settings[key][sub_key] = sub_value
                return settings
        except (EOFError, pickle.UnpicklingError):
            return defaults # Return defaults if file is corrupt
    return defaults

def save_settings(settings_data):
    """
    Saves the application settings dictionary to its pickle file.
    
    Args:
        settings_data (dict): The settings dictionary to save.
    """
    with open(SETTINGS_FILE, 'wb') as f:
        pickle.dump(settings_data, f)

def get_next_document_number(doc_type="invoice"):
    """
    Atomically retrieves, increments, and saves the next sequential
    document number for invoices or quotes.
    
    This function also handles automatic year change reset.
    (e.g., F2024/999 -> F2025/001).

    Args:
        doc_type (str): 'invoice' or 'quote'.

    Returns:
        str: The formatted, incremented document number (e.g., "F2025/001").
    """
    # This is "atomic" because it loads, modifies, and saves in one operation
    settings = load_settings()
    
    current_year = datetime.now().year
    
    if doc_type == "invoice":
        key = 'last_invoice_num'
        prefix_key = 'invoice_prefix'
        default_prefix = f"F{current_year}/"
    else: # 'quote'
        key = 'last_quote_num'
        prefix_key = 'quote_prefix'
        default_prefix = f"P{current_year}/"

    prefix = settings.get(prefix_key, default_prefix)
    
    # Check if the year has changed since the last number was issued
    if str(current_year) not in prefix:
        # Reset counter and update prefix to the new year
        settings[key] = 0
        settings[prefix_key] = default_prefix
        prefix = default_prefix

    # Increment and save
    new_number = settings.get(key, 0) + 1
    settings[key] = new_number
    
    save_settings(settings)
    
    # Return formatted number (e.g., F2025/001)
    return f"{prefix}{str(new_number).zfill(3)}"