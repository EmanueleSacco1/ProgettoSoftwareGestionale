import uuid
from decimal import Decimal, InvalidOperation

# Import the centralized database access module using a relative import
from . import persistence as db

# --- CRUD Functions ---

def create_articolo(data):
    """
    Creates a new inventory item.
    
    Args:
        data (dict): Contains 'nome', 'codice', 'descrizione',
                     'prezzo_acquisto', 'qta_in_stock'.
    Returns:
        dict: The newly created item.
    Raises:
        ValueError: If 'nome' is missing or price/quantity are not valid numbers.
    """
    articoli = db.load_data(db.MAGAZZINO_DB)
    
    try:
        # Create the new item dictionary, ensuring types are correct
        new_articolo = {
            'id': str(uuid.uuid4()),
            'nome': data.get('nome'),
            'codice': data.get('codice', ''),
            'descrizione': data.get('descrizione', ''),
            'prezzo_acquisto': Decimal(str(data.get('prezzo_acquisto', '0'))),
            'qta_in_stock': Decimal(str(data.get('qta_in_stock', '0')))
        }
    except InvalidOperation as e:
        raise ValueError(f"Invalid price or quantity: {e}")

    if not new_articolo['nome']:
        raise ValueError("Name is mandatory.")

    articoli.append(new_articolo)
    db.save_data(db.MAGAZZINO_DB, articoli)
    return new_articolo

def get_all_articoli():
    """
    Retrieves all items from the warehouse.

    Returns:
        list: A list of all item dictionaries.
    """
    return db.load_data(db.MAGAZZINO_DB)

def find_articolo_by_id(articolo_id):
    """
    Finds a single item by its unique ID.

    Args:
        articolo_id (str): The 'id' of the item to find.

    Returns:
        dict: The item dictionary if found, else None.
    """
    articoli = db.load_data(db.MAGAZZINO_DB)
    for art in articoli:
        if art.get('id') == articolo_id:
            return art
    return None

def update_articolo(articolo_id, updated_data):
    """
    Updates an item's descriptive data (name, code, price).
    This function *does not* update stock quantity. Use update_stock for that.

    Args:
        articolo_id (str): The 'id' of the item to update.
        updated_data (dict): A dictionary of fields to update.

    Returns:
        dict: The updated item dictionary, or None if not found.
    Raises:
        ValueError: If price is not a valid number.
    """
    articoli = db.load_data(db.MAGAZZINO_DB)
    articolo_found = False
    
    try:
        for i, art in enumerate(articoli):
            if art.get('id') == articolo_id:
                # Update fields but explicitly exclude qta_in_stock
                # Stock should only be changed via update_stock()
                if 'qta_in_stock' in updated_data:
                    del updated_data['qta_in_stock']
                    
                art.update(updated_data)
                
                # Ensure price is converted back to Decimal
                if 'prezzo_acquisto' in updated_data:
                    art['prezzo_acquisto'] = Decimal(str(updated_data['prezzo_acquisto']))
                    
                articoli[i] = art
                articolo_found = True
                break
                
        if articolo_found:
            db.save_data(db.MAGAZZINO_DB, articoli)
            return articoli[i]
        return None
        
    except InvalidOperation as e:
         raise ValueError(f"Invalid price: {e}")

def delete_articolo(articolo_id):
    """
    Removes an item from the database by its ID.

    Args:
        articolo_id (str): The 'id' of the item to delete.

    Returns:
        bool: True if deletion was successful, False otherwise.
    """
    articoli = db.load_data(db.MAGAZZINO_DB)
    # Rebuild the list excluding the item to delete
    new_articoli = [art for art in articoli if art.get('id') != articolo_id]
    
    if len(new_articoli) < len(articoli):
        db.save_data(db.MAGAZZINO_DB, new_articoli)
        return True
    return False

def search_articoli(query):
    """
    Searches items for a query string in name or code.
    The search is case-insensitive.

    Args:
        query (str): The search term.

    Returns:
        list: A list of matching item dictionaries.
    """
    articoli = db.load_data(db.MAGAZZINO_DB)
    query = query.lower()
    results = []
    
    for art in articoli:
        if (query in art.get('nome', '').lower() or
            query in art.get('codice', '').lower()):
            results.append(art)
    return results

# --- Stock Management ---

def update_stock(articolo_id, quantita_delta):
    """
    Adjusts the stock for an item by a delta (positive or negative).
    This is the only function that should modify 'qta_in_stock'.

    Args:
        articolo_id (str): The 'id' of the item to adjust.
        quantita_delta (Decimal, float, or str): The amount to add (e.g., 10) or
                                                 subtract (e.g., -1.5).

    Returns:
        tuple (bool, str): (True, "Success message") or (False, "Error message").
    """
    articoli = db.load_data(db.MAGAZZINO_DB)
    articolo_found = False
    
    try:
        qta_delta = Decimal(str(quantita_delta))
    except InvalidOperation as e:
        return False, f"Invalid quantity: {e}"

    for i, art in enumerate(articoli):
        if art.get('id') == articolo_id:
            current_stock = art.get('qta_in_stock', Decimal('0'))
            new_stock = current_stock + qta_delta
            
            if new_stock < 0:
                # Prevent negative stock
                return False, f"Insufficient stock. Available: {current_stock}"
                
            art['qta_in_stock'] = new_stock
            articoli[i] = art
            articolo_found = True
            break
            
    if articolo_found:
        db.save_data(db.MAGAZZINO_DB, articoli)
        return True, f"Stock updated. New quantity: {new_stock}"
    return False, "Item not found."