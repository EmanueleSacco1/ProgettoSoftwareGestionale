import os
import pickle
from datetime import date

# Directory per i file pickle
DATA_DIR = 'data_pickle'
os.makedirs(DATA_DIR, exist_ok=True)

def load_data(filename):
    try:
        with open(os.path.join(DATA_DIR, filename), 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return []

def save_data(data, filename):
    with open(os.path.join(DATA_DIR, filename), 'wb') as f:
        pickle.dump(data, f)

# Classe Fattura senza dipendenze da Django
class Fattura:
    def __init__(self, numero, data, nome, cognome, nome_ditta):
        self.numero = numero
        self.data = data
        self.nome = nome
        self.cognome = cognome
        self.nome_ditta = nome_ditta

# Classe TariffaFatt per le tariffe di ogni fattura
class TariffaFatt:
    def __init__(self, fattura_id, descrizione, prezzo):
        self.fattura_id = fattura_id
        self.descrizione = descrizione
        self.prezzo = prezzo

# Classe FatturaAdmin per gestire le fatture
class FatturaAdmin:
    def __init__(self):
        self.fatture = load_data('fatture.pkl')
        self.tariffe = load_data('tariffe_fatt.pkl')

    def list_fatture(self):
        return [(fattura.numero, fattura.data, fattura.nome, fattura.cognome, fattura.nome_ditta) for fattura in self.fatture]

    def add_fattura(self, numero, data, nome, cognome, nome_ditta):
        new_fattura = Fattura(numero=numero, data=data, nome=nome, cognome=cognome, nome_ditta=nome_ditta)
        self.fatture.append(new_fattura)
        save_data(self.fatture, 'fatture.pkl')

    def add_tariffa(self, fattura_id, descrizione, prezzo):
        new_tariffa = TariffaFatt(fattura_id=fattura_id, descrizione=descrizione, prezzo=prezzo)
        self.tariffe.append(new_tariffa)
        save_data(self.tariffe, 'tariffe_fatt.pkl')

    def generate_pdf(self, fattura_id):
        # Simulazione della generazione di un PDF per la fattura
        fattura = next((f for f in self.fatture if f.numero == fattura_id), None)
        if fattura:
            # Simulazione della logica di generazione del PDF
            print(f"Generazione PDF per Fattura #{fattura.numero}: {fattura.nome} {fattura.cognome}, Ditta: {fattura.nome_ditta}")

# Esempio di utilizzo
if __name__ == "__main__":
    fattura_admin = FatturaAdmin()

    # Aggiungi una nuova fattura
    fattura_admin.add_fattura(numero="F001", data=date.today(), nome="Mario", cognome="Rossi", nome_ditta="Ditta Rossi")

    # Aggiungi una tariffa alla fattura
    fattura_admin.add_tariffa(fattura_id="F001", descrizione="Servizio di consulenza", prezzo=100.0)

    # Visualizza tutte le fatture
    fatture = fattura_admin.list_fatture()
    for numero, data, nome, cognome, nome_ditta in fatture:
        print(f"Numero: {numero}, Data: {data}, Nome: {nome}, Cognome: {cognome}, Ditta: {nome_ditta}")

    # Genera il PDF per una fattura specifica
    fattura_admin.generate_pdf("F001")
