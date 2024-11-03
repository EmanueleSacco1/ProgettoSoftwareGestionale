# -*- coding: utf-8 -*-
import pickle
import datetime as dt
import os

# Directory dove salvare i dati
DATA_DIR = 'data_pickle'
os.makedirs(DATA_DIR, exist_ok=True)


# Funzioni per salvare e caricare i dati
def save_data(data, filename):
    with open(os.path.join(DATA_DIR, filename), 'wb') as f:
        pickle.dump(data, f)


def load_data(filename):
    try:
        with open(os.path.join(DATA_DIR, filename), 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return []


# Classe Appuntamento senza dipendenze da Django
class Appuntamento:
    _id_counter = 1  # Per simulare un ID autoincrementante

    def __init__(self, nome, day, orario_inizio=dt.time(0, 0), orario_fine=dt.time(0, 0), note=""):
        self.id = Appuntamento._id_counter
        Appuntamento._id_counter += 1
        self.nome = nome
        self.day = day
        self.orario_inizio = orario_inizio
        self.orario_fine = orario_fine
        self.note = note

    def check_overlap(self, fixed_start, fixed_end, new_start, new_end):
        # Verifica sovrapposizioni con i limiti degli orari
        if (new_start >= fixed_start and new_start < fixed_end) or (new_end > fixed_start and new_end <= fixed_end):
            return True
        if new_start <= fixed_start and new_end >= fixed_end:
            return True
        return False

    def validate(self, existing_events):
        # Verifica che orario_fine non sia precedente a orario_inizio
        if self.orario_fine <= self.orario_inizio:
            raise ValueError('Un orario di fine non può precedere o essere uguale a quello di inizio')

        # Controlla per sovrapposizioni
        for event in existing_events:
            if self.day == event.day and self.check_overlap(event.orario_inizio, event.orario_fine, self.orario_inizio,
                                                            self.orario_fine):
                raise ValueError(
                    f'Sovrapposizione con evento esistente: {event.day}, {event.orario_inizio}-{event.orario_fine}'
                )


# Classe Agenda per gestire l'elenco degli appuntamenti
class Agenda:
    def __init__(self):
        self.appuntamenti = load_data('appuntamenti.pkl')

    def aggiungi_appuntamento(self, appuntamento):
        # Validazione appuntamento prima dell'aggiunta
        appuntamento.validate(self.appuntamenti)
        self.appuntamenti.append(appuntamento)
        save_data(self.appuntamenti, 'appuntamenti.pkl')

    def visualizza_appuntamenti(self):
        for appuntamento in self.appuntamenti:
            print(
                f"{appuntamento.nome} - {appuntamento.day} dalle {appuntamento.orario_inizio} alle {appuntamento.orario_fine}")


# Esempio di utilizzo
if __name__ == "__main__":
    agenda = Agenda()
    today = dt.date.today()

    # Crea un nuovo appuntamento
    nuovo_appuntamento = Appuntamento(
        nome="Riunione Team",
        day=today,
        orario_inizio=dt.time(10, 0),
        orario_fine=dt.time(11, 0),
        note="Discussione strategia"
    )

    try:
        # Aggiunge l'appuntamento all'agenda
        agenda.aggiungi_appuntamento(nuovo_appuntamento)
    except ValueError as e:
        print(f"Errore: {e}")

    # Visualizza tutti gli appuntamenti
    agenda.visualizza_appuntamenti()
