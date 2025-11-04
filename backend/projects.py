import os
import uuid
from datetime import date
import shutil

# Import the centralized database access module using a relative import
from . import persistence as db
from . import address_book as db_rubrica

# --- Constants ---
STATI_PROGETTO = ["In corso", "Completato", "In attesa", "Annullato"]
PROJECT_FILES_DIR = "PROGETTI_FILES" # Base directory for storing project files

# --- Project CRUD Functions ---

def create_project(project_data):
    """
    Creates a new project.
    
    Args:
        project_data (dict): Contains 'name', 'client_id', 'description', 'tariffa_oraria'.
    
    Returns:
        dict: The newly created project dictionary.
    
    Raises:
        ValueError: If the 'client_id' does not exist in the address book.
    """
    projects = db.load_data(db.PROGETTI_DB)
    
    # Validate client existence
    client = db_rubrica.find_contact_by_id(project_data.get('client_id'))
    if not client:
        raise ValueError(f"Cliente con ID {project_data.get('client_id')} non trovato.")

    # Build the new project object
    new_project = {
        'id': str(uuid.uuid4()),
        'name': project_data['name'],
        'client_id': project_data['client_id'],
        'description': project_data.get('description', ''),
        'status': "In corso",  # Default status
        'tariffa_oraria': float(project_data.get('tariffa_oraria', 0.0)),
        'fasi': [],           # List to store project phases
        'attivita': [],       # List to store time tracking entries
        'file_archiviati': [] # List to store filenames
    }
    
    projects.append(new_project)
    db.save_data(db.PROGETTI_DB, projects)
    return new_project

def get_all_projects(status_filter=None):
    """
    Retrieves all projects, optionally filtering by status.

    Args:
        status_filter (str, optional): A valid status (e.g., "In corso").

    Returns:
        list: A list of project dictionaries.
    """
    projects = db.load_data(db.PROGETTI_DB)
    if status_filter:
        return [p for p in projects if p.get('status') == status_filter]
    return projects

def find_project_by_id(project_id):
    """
    Finds a single project by its unique ID.

    Args:
        project_id (str): The 'id' of the project to find.

    Returns:
        dict: The project dictionary if found, else None.
    """
    projects = db.load_data(db.PROGETTI_DB)
    for project in projects:
        if project.get('id') == project_id:
            return project
    return None

def update_project(project_id, updated_data):
    """
    Updates a project's top-level data (name, status, tariffa).
    This function does not modify nested lists (fasi, attivita, file).

    Args:
        project_id (str): The 'id' of the project to update.
        updated_data (dict): A dictionary of fields to update.

    Returns:
        dict: The updated project dictionary, or None if not found.
        
    Raises:
        ValueError: If 'status' is provided but is not a valid status.
    """
    projects = db.load_data(db.PROGETTI_DB)
    project_found = False
    
    for i, project in enumerate(projects):
        if project.get('id') == project_id:
            # Validate status if it's being changed
            if 'status' in updated_data and updated_data['status'] not in STATI_PROGETTO:
                raise ValueError(f"Stato '{updated_data['status']}' non valido.")
                
            project.update(updated_data)
            projects[i] = project
            project_found = True
            break
            
    if project_found:
        db.save_data(db.PROGETTI_DB, projects)
        return projects[i]
    return None

def delete_project(project_id):
    """
    Deletes a project by ID.
    This also attempts to delete the associated project file directory.

    Args:
        project_id (str): The 'id' of the project to delete.

    Returns:
        bool: True if deletion was successful, False otherwise.
    """
    projects = db.load_data(db.PROGETTI_DB)
    new_projects = [p for p in projects if p.get('id') != project_id]
    
    if len(new_projects) < len(projects):
        db.save_data(db.PROGETTI_DB, new_projects)
        
        # Also delete associated files directory
        try:
            project_files_path = get_project_files_path(project_id)
            if os.path.exists(project_files_path):
                # Recursively remove the directory and all its contents
                shutil.rmtree(project_files_path)
        except Exception as e:
            # Log the error but don't stop. The project data is already deleted.
            print(f"Warning: Could not delete project file directory. {e}")
            
        return True
    return False

# --- Phase (Fasi) Management ---

def add_fase_to_project(project_id, nome_fase, scadenza):
    """
    Adds a new phase to a project's 'fasi' list.

    Args:
        project_id (str): The project to modify.
        nome_fase (str): The name of the new phase.
        scadenza (str): The due date in 'YYYY-MM-DD' format (or None).

    Returns:
        tuple (bool, str): (True, "Success message") or (False, "Error message").
    """
    project = find_project_by_id(project_id)
    if not project:
        return False, "Progetto non trovato."
        
    fase = {
        'id': str(uuid.uuid4()),
        'nome': nome_fase,
        'scadenza': scadenza,
        'completata': False
    }
    project['fasi'].append(fase)
    
    # update_project saves the entire project list to the database
    update_project(project_id, project) 
    return True, "Fase aggiunta."

def toggle_fase_status(project_id, fase_id):
    """
    Toggles the 'completata' status of a phase (True -> False, False -> True).

    Args:
        project_id (str): The project ID.
        fase_id (str): The phase 'id' to toggle.

    Returns:
        tuple (bool, str): (True, "Success message") or (False, "Error message").
    """
    project = find_project_by_id(project_id)
    if not project: return False, "Progetto non trovato."

    fase_found = False
    for fase in project['fasi']:
        if fase['id'] == fase_id:
            fase['completata'] = not fase['completata'] # The toggle logic
            fase_found = True
            break
    
    if fase_found:
        update_project(project_id, project)
        return True, "Stato fase aggiornato."
    return False, "Fase non trovata."

def delete_fase(project_id, fase_id):
    """
    Removes a phase from a project.

    Args:
        project_id (str): The project ID.
        fase_id (str): The phase 'id' to delete.

    Returns:
        tuple (bool, str): (True, "Success message") or (False, "Error message").
    """
    project = find_project_by_id(project_id)
    if not project: return False, "Progetto non trovato."
    
    original_len = len(project['fasi'])
    # Rebuild the list without the matching phase
    project['fasi'] = [f for f in project['fasi'] if f['id'] != fase_id]
    
    if len(project['fasi']) < original_len:
        update_project(project_id, project)
        return True, "Fase eliminata."
    return False, "Fase non trovata."


# --- Time Tracking (Attività) Management ---

def add_attivita_to_project(project_id, data, ore, descrizione, fatturabile=True):
    """
    Adds a new time tracking entry (attivita) to a project.

    Args:
        project_id (str): The project to add to.
        data (str): Date in 'YYYY-MM-DD' format.
        ore (float or str): Number of hours.
        descrizione (str): Description of the work.
        fatturabile (bool): Whether the time is billable.

    Returns:
        tuple (bool, str): (True, "Success message") or (False, "Error message").
    """
    project = find_project_by_id(project_id)
    if not project:
        return False, "Progetto non trovato."
        
    try:
        ore_float = float(ore)
    except ValueError:
        return False, "Le ore devono essere un numero."

    attivita = {
        'id': str(uuid.uuid4()),
        'data': data,
        'ore': ore_float,
        'descrizione': descrizione,
        'fatturabile': fatturabile
    }
    project['attivita'].append(attivita)
    update_project(project_id, project) # Save changes
    return True, "Attività aggiunta."

def delete_attivita(project_id, attivita_id):
    """
    Removes a time tracking entry from a project.

    Args:
        project_id (str): The project ID.
        attivita_id (str): The 'id' of the activity to delete.

    Returns:
        tuple (bool, str): (True, "Success message") or (False, "Error message").
    """
    project = find_project_by_id(project_id)
    if not project: return False, "Progetto non trovato."
    
    original_len = len(project['attivita'])
    project['attivita'] = [a for a in project['attivita'] if a['id'] != attivita_id]
    
    if len(project['attivita']) < original_len:
        update_project(project_id, project)
        return True, "Attività eliminata."
    return False, "Attività non trovata."


# --- File Management ---

def get_project_files_path(project_id):
    """
    Gets the dedicated file storage path for a project.
    Ensures the base 'PROGETTI_FILES' and the specific project directory exist.

    Args:
        project_id (str): The project's unique ID.

    Returns:
        str: The full path to the project's directory.
    """
    os.makedirs(PROJECT_FILES_DIR, exist_ok=True)
    project_path = os.path.join(PROJECT_FILES_DIR, project_id)
    os.makedirs(project_path, exist_ok=True) # Ensure the specific folder exists
    return project_path
    
def add_file_to_project(project_id, source_file_path):
    """
    Copies a file from a source path into the project's dedicated
    file directory and registers its name in the project data.

    Args:
        project_id (str): The project to add the file to.
        source_file_path (str): The full path of the file to copy.

    Returns:
        tuple (bool, str): (True, "Success message") or (False, "Error message").
    """
    project = find_project_by_id(project_id)
    if not project:
        return False, "Progetto non trovato."
        
    if not os.path.exists(source_file_path):
        return False, "File sorgente non trovato."
        
    filename = os.path.basename(source_file_path)
    
    # Create the project's specific directory
    project_files_path = get_project_files_path(project_id)
    destination_path = os.path.join(project_files_path, filename)
    
    # Prevent overwriting
    if os.path.exists(destination_path):
        return False, f"Un file con nome '{filename}' esiste già in questo progetto."

    try:
        # Perform the physical file copy
        shutil.copy(source_file_path, destination_path)
    except Exception as e:
        return False, f"Impossibile copiare il file: {e}"

    # If copy succeeds, register the filename in the project data
    if filename not in project['file_archiviati']:
        project['file_archiviati'].append(filename)
        update_project(project_id, project)
        return True, f"File copiato e registrato con successo."
    
    return False, "File già registrato (ma la copia è stata eseguita)."

def delete_file_from_project(project_id, filename):
    """
    Removes a file from the project's directory and its registration
    from the project data.

    Args:
        project_id (str): The project ID.
        filename (str): The name of the file to delete (just the name, not path).

    Returns:
        tuple (bool, str): (True, "Success message") or (False, "Error message").
    """
    project = find_project_by_id(project_id)
    if not project:
        return False, "Progetto non trovato."
    
    if filename in project['file_archiviati']:
        # 1. Remove from data registration
        project['file_archiviati'].remove(filename)
        update_project(project_id, project)
        
        # 2. Remove from disk
        try:
            file_path = os.path.join(get_project_files_path(project_id), filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            # Report error, but the data registration is already removed,
            # so we still return True (partial success)
            return True, f"Registrazione rimossa, ma errore eliminazione file: {e}"
            
        return True, "File e registrazione rimossi."
    return False, "File non trovato nella lista del progetto."


# --- Dashboard Calculation ---

def calculate_project_totals(project_id):
    """
    Calculates summary statistics for a project's dashboard.
    Distinguishes between total hours and billable hours.

    Args:
        project_id (str): The project ID to calculate.

    Returns:
        dict: A dictionary of calculated totals (total_ore, ore_fatturabili, 
              total_costo, fasi_completate, fasi_totali, tariffa_oraria).
              Returns None if project not found.
    """
    project = find_project_by_id(project_id)
    if not project:
        return None
        
    # 1. Calculate Hours
    total_ore = 0.0
    ore_fatturabili = 0.0
    for a in project.get('attivita', []):
        total_ore += a['ore']
        # Handle old data created before 'fatturabile' flag existed
        if a.get('fatturabile', True): 
            ore_fatturabili += a['ore']

    # 2. Calculate Cost
    tariffa = project.get('tariffa_oraria', 0.0)
    # Cost is based *only* on billable hours
    total_costo = ore_fatturabili * tariffa
    
    # 3. Phase Progress
    fasi_totali = len(project.get('fasi', []))
    fasi_completate = sum(1 for f in project.get('fasi', []) if f['completata'])
    
    return {
        'total_ore': total_ore,
        'ore_fatturabili': ore_fatturabili,
        'total_costo': total_costo,
        'fasi_completate': fasi_completate,
        'fasi_totali': fasi_totali,
        'tariffa_oraria': tariffa
    }