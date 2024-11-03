import os
import pickle

# Trova il percorso del Desktop in modo compatibile per Windows, macOS e Linux
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

# Percorso della cartella "Gestionale ingegnere" sul Desktop
DATA_DIR = os.path.join(desktop_path, "Gestionale ingegnere")

# Crea la cartella "Gestionale ingegnere" se non esiste
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


def save_data(data, filename):
    """Salva i dati in formato pickle nella cartella specificata."""
    with open(os.path.join(DATA_DIR, f"{filename}.pkl"), 'wb') as f:
        pickle.dump(data, f)


def load_data(filename):
    """Carica i dati da un file pickle nella cartella specificata.

    Restituisce una lista vuota se il file non esiste.
    """
    try:
        with open(os.path.join(DATA_DIR, f"{filename}.pkl"), 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return []
