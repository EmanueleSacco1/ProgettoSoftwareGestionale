import os
import pickle
from dataclasses import dataclass, field
from datetime import date

# Directory per i file pickle
DATA_DIR = 'data_pickle'
os.makedirs(DATA_DIR, exist_ok=True)

# Funzioni di validazione
def validate_price(value):
    if value < 0:
        raise ValueError('questo campo non può essere negativo')

# Classe Fattura
@dataclass
class Fattura:
    nome: str = field(default=None)
    cognome: str = field(default=None)
    nome_ditta: str = field(default=None)
    citta: str = field(default=None)
    via: str = field(default=None)
    num_civico: int = field(default=None)
    cap: int = field(default=None)
    partita_iva: int = field(default=None)
    cod_fiscale: str = field(default=None)
    cod_cliente: str = field(default=None)
    numero: int = field(default=None)
    data: date = field(default=None)
    descrizione_pag: str = field(default=None)
    banca: str = field(default=None)

    def __post_init__(self):
        validate_price(self.num_civico)
        validate_price(self.cap)
        validate_price(self.partita_iva)
        validate_price(self.numero)

# Classe TariffaFatt
@dataclass
class TariffaFatt:
    descrizione_prod: str = field(default=None)
    quantita: int = field(default=None)
    prezzo: float = field(default=None)
    fattura: Fattura = field(default=None)

    def __post_init__(self):
        validate_price(self.quantita)
        validate_price(self.prezzo)

# Funzione per gestire le fatture
class FatturaAdmin:
    def __init__(self):
        self.fatture = self.load_data('fatture.pkl')
        self.tariffe = self.load_data('tariffe_fatt.pkl')

    def load_data(self, filename):
        try:
            with open(os.path.join(DATA_DIR, filename), 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            return []

    def save_data(self, data, filename):
        with open(os.path.join(DATA_DIR, filename), 'wb') as f:
            pickle.dump(data, f)

    def add_fattura(self, **kwargs):
        new_fattura = Fattura(**kwargs)
        self.fatture.append(new_fattura)
        self.save_data(self.fatture, 'fatture.pkl')

    def add_tariffa(self, fattura, **kwargs):
        new_tariffa = TariffaFatt(fattura=fattura, **kwargs)
        self.tariffe.append(new_tariffa)
        self.save_data(self.tariffe, 'tariffe_fatt.pkl')

# Esempio di utilizzo
if __name__ == "__main__":
    fattura_admin = FatturaAdmin()

    # Aggiungi una nuova fattura
    try:
        fattura_admin.add_fattura(
            nome="Mario",
            cognome="Rossi",
            nome_ditta="Ditta Rossi",
            citta="Milano",
            via="Via Roma",
            num_civico=10,
            cap=20100,
            partita_iva=12345678901,
            cod_fiscale="RSSMRA80A01H501Z",
            cod_cliente="C001",
            numero=1,
            data=date.today(),
            descrizione_pag="Pagamento per servizi",
            banca="Banca Popolare"
        )
    except ValueError as e:
        print(f"Errore durante l'aggiunta della fattura: {e}")

    # Aggiungi una tariffa alla fattura
    fattura = fattura_admin.fatture[0]  # Assume che ci sia almeno una fattura
    try:
        fattura_admin.add_tariffa(
            fattura=fattura,
            descrizione_prod="Servizio di consulenza",
            quantita=2,
            prezzo=100.00
        )
    except ValueError as e:
        print(f"Errore durante l'aggiunta della tariffa: {e}")

    # Visualizza tutte le fatture
    for fattura in fattura_admin.fatture:
        print(f"Fattura #{fattura.numero}: {fattura.nome} {fattura.cognome}, Ditta: {fattura.nome_ditta}")
