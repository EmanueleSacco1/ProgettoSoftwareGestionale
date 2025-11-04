import os
import uuid
import csv
import pandas as pd

# Import the centralized database access module using a relative import
from . import persistence as db

# --- CRUD Functions ---

def create_contact(contact_data):
    """
    Adds a new contact to the database.
    
    Args:
        contact_data (dict): A dictionary containing all contact fields.
                             (name, company, vat_id, email, phone, etc.)
    Returns:
        dict: The created contact data, including its new unique ID.
    """
    contacts = db.load_data(db.RUBRICA_DB)
    
    # Assign a unique ID
    contact_data['id'] = str(uuid.uuid4())
    
    contacts.append(contact_data)
    db.save_data(db.RUBRICA_DB, contacts)
    return contact_data

def get_all_contacts():
    """
    Retrieves all contacts from the database.

    Returns:
        list: A list of all contact dictionaries.
    """
    return db.load_data(db.RUBRICA_DB)

def find_contact_by_id(contact_id):
    """
    Finds a single contact by its unique ID.

    Args:
        contact_id (str): The 'id' of the contact to find.

    Returns:
        dict: The contact dictionary if found, else None.
    """
    contacts = db.load_data(db.RUBRICA_DB)
    for contact in contacts:
        if contact.get('id') == contact_id:
            return contact
    return None

def search_contacts(query):
    """
    Searches contacts for a query string in multiple fields.
    The search is case-insensitive.

    Args:
        query (str): The search term.

    Returns:
        list: A list of matching contact dictionaries.
    """
    contacts = db.load_data(db.RUBRICA_DB)
    query = query.lower()
    results = []
    
    for contact in contacts:
        if (query in contact.get('name', '').lower() or
            query in contact.get('company', '').lower() or
            query in contact.get('vat_id', '').lower() or
            query in contact.get('email', '').lower()):
            results.append(contact)
    return results

def update_contact(contact_id, updated_data):
    """
    Finds a contact by ID and updates it with new data.

    Args:
        contact_id (str): The 'id' of the contact to update.
        updated_data (dict): A dictionary of fields to update.

    Returns:
        dict: The updated contact dictionary, or None if not found.
    """
    contacts = db.load_data(db.RUBRICA_DB)
    contact_found = False
    
    for i, contact in enumerate(contacts):
        if contact.get('id') == contact_id:
            # Update the existing dictionary with new values
            contact.update(updated_data)
            contacts[i] = contact
            contact_found = True
            break
            
    if contact_found:
        db.save_data(db.RUBRICA_DB, contacts)
        return contacts[i]
    else:
        return None

def delete_contact(contact_id):
    """
    Removes a contact from the database by its ID.

    Args:
        contact_id (str): The 'id' of the contact to delete.

    Returns:
        bool: True if deletion was successful, False otherwise.
    """
    contacts = db.load_data(db.RUBRICA_DB)
    
    # Create a new list excluding the contact to be deleted
    new_contacts = [c for c in contacts if c.get('id') != contact_id]
    
    if len(new_contacts) < len(contacts):
        # The list is shorter, meaning the contact was found and removed
        db.save_data(db.RUBRICA_DB, new_contacts)
        return True  # Success
    else:
        return False # Not found

# --- Import/Export Functions ---

def export_to_csv(filename='rubrica_export.csv'):
    """
    Exports the entire address book to a CSV file using pandas.

    Args:
        filename (str): The target file name.

    Returns:
        tuple (bool, str): (True, "Success message") or (False, "Error message").
    """
    contacts = db.load_data(db.RUBRICA_DB)
    if not contacts:
        return False, "Nessun contatto da esportare."
        
    try:
        df = pd.DataFrame(contacts)
        # Use utf-8-sig to include a BOM for Excel compatibility
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        return True, f"Esportato con successo in {filename}"
    except Exception as e:
        return False, f"Errore durante l'esportazione CSV: {e}"

def export_to_excel(filename='rubrica_export.xlsx'):
    """
    Exports the entire address book to an Excel file using pandas.
    The internal 'id' column is dropped.

    Args:
        filename (str): The target file name.

    Returns:
        tuple (bool, str): (True, "Success message") or (False, "Error message").
    """
    contacts = db.load_data(db.RUBRICA_DB)
    if not contacts:
        return False, "Nessun contatto da esportare."
        
    try:
        df = pd.DataFrame(contacts)
        # Drop the internal ID from the export
        if 'id' in df.columns:
            df = df.drop(columns=['id'])
            
        df.to_excel(filename, index=False)
        return True, f"Esportato con successo in {filename}"
    except Exception as e:
        return False, f"Errore durante l'esportazione Excel: {e}"

def import_from_csv(filename):
    """
    Imports contacts from a CSV file and appends them to the address book.
    Assigns new unique IDs to all imported contacts.

    Args:
        filename (str): The source CSV file name.

    Returns:
        tuple (int, str): (count, "Success/Error message").
    """
    try:
        with open(filename, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            new_contacts = [row for row in reader]
        
        if not new_contacts:
            return 0, "File vuoto o formato non valido."

        contacts = db.load_data(db.RUBRICA_DB)
        imported_count = 0
        for contact_data in new_contacts:
            if 'name' in contact_data: # Basic validation
                contact_data['id'] = str(uuid.uuid4()) # Assign new ID
                contacts.append(contact_data)
                imported_count += 1
        
        db.save_data(db.RUBRICA_DB, contacts)
        return imported_count, f"Importati {imported_count} contatti."
        
    except FileNotFoundError:
        return 0, "File non trovato."
    except Exception as e:
        return 0, f"Errore durante l'importazione: {e}"

def import_from_excel(filename):
    """
    Imports contacts from an Excel file and appends them to the address book.
    Assigns new unique IDs to all imported contacts.

    Args:
        filename (str): The source Excel file name.

    Returns:
        tuple (int, str): (count, "Success/Error message").
    """
    try:
        df = pd.read_excel(filename)
        # Convert DataFrame rows to a list of dictionaries
        new_contacts = df.to_dict('records')

        if not new_contacts:
            return 0, "File vuoto o formato non valido."

        contacts = db.load_data(db.RUBRICA_DB)
        imported_count = 0
        for contact_data in new_contacts:
            if 'name' in contact_data: # Basic validation
                contact_data['id'] = str(uuid.uuid4()) # Assign new ID
                contacts.append(contact_data)
                imported_count += 1
                
        db.save_data(db.RUBRICA_DB, contacts)
        return imported_count, f"Importati {imported_count} contatti."

    except FileNotFoundError:
        return 0, "File non trovato."
    except Exception as e:
        return 0, f"Errore durante l'importazione: {e}"