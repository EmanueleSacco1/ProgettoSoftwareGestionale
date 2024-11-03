import pickle
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def save_data(data, filename):
    file_path = os.path.join(BASE_DIR, f"{filename}.pkl")
    with open(file_path, 'wb') as file:
        pickle.dump(data, file)

def load_data(filename):
    file_path = os.path.join(BASE_DIR, f"{filename}.pkl")
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            return pickle.load(file)
    return []
