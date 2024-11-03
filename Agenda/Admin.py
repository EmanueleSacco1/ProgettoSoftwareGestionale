import pickle
import datetime
import calendar
import os
from calendar import HTMLCalendar

# Definiamo la directory dove verranno salvati i dati
DATA_DIR = 'data_pickle'
os.makedirs(DATA_DIR, exist_ok=True)


# Funzione per salvare e caricare dati in file pickle
def save_data(data, filename):
    with open(os.path.join(DATA_DIR, filename), 'wb') as f:
        pickle.dump(data, f)


def load_data(filename):
    try:
        with open(os.path.join(DATA_DIR, filename), 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None


# Classe per gli appuntamenti
class Appuntamento:
    def __init__(self, nome, day, orario_inizio, orario_fine, note):
        self.nome = nome
        self.day = day
        self.orario_inizio = orario_inizio
        self.orario_fine = orario_fine
        self.note = note


# Funzione per visualizzare il calendario
class Agenda:
    def __init__(self):
        self.appuntamenti = load_data('appuntamenti.pkl') or []

    def aggiungi_appuntamento(self, appuntamento):
        self.appuntamenti.append(appuntamento)
        save_data(self.appuntamenti, 'appuntamenti.pkl')

    def visualizza_calendario(self, year, month):
        cal = HTMLCalendar()
        html_calendar = cal.formatmonth(year, month, withyear=True)
        html_calendar = html_calendar.replace('<td ', '<td  width="150" height="150"')
        return html_calendar

    def visualizza_appuntamenti(self):
        for appuntamento in self.appuntamenti:
            print(
                f"{appuntamento.nome} - {appuntamento.day} dalle {appuntamento.orario_inizio} alle {appuntamento.orario_fine}")


# Funzione per cambiare mese
def cambia_mese(d, direction='next'):
    if direction == 'next':
        last_day = calendar.monthrange(d.year, d.month)
        next_month = datetime.date(year=d.year, month=d.month, day=last_day[1]) + datetime.timedelta(days=1)
        return datetime.date(year=next_month.year, month=next_month.month, day=1)
    elif direction == 'previous':
        previous_month = datetime.date(year=d.year, month=d.month, day=1) - datetime.timedelta(days=1)
        return datetime.date(year=previous_month.year, month=previous_month.month, day=1)
    return d


# Esempio di utilizzo
if __name__ == "__main__":
    agenda = Agenda()
    today = datetime.date.today()

    # Visualizza il calendario per il mese corrente
    print(agenda.visualizza_calendario(today.year, today.month))

    # Aggiunge un appuntamento di esempio
    nuovo_appuntamento = Appuntamento(
        nome="Riunione Team",
        day=today,
        orario_inizio="10:00",
        orario_fine="11:00",
        note="Discussione strategia"
    )
    agenda.aggiungi_appuntamento(nuovo_appuntamento)

    # Visualizza gli appuntamenti
    agenda.visualizza_appuntamenti()

    # Cambia mese e visualizza il nuovo mese
    prossimo_mese = cambia_mese(today, direction='next')
    print(agenda.visualizza_calendario(prossimo_mese.year, prossimo_mese.month))
