from calendar import HTMLCalendar
from datetime import datetime as dtime, date
import os
import pickle

# Funzioni per salvare e caricare eventi da file pickle
DATA_DIR = 'data_pickle'
os.makedirs(DATA_DIR, exist_ok=True)


def load_data(filename):
    try:
        with open(os.path.join(DATA_DIR, filename), 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return []


class Appuntamento:
    def __init__(self, nome, day, orario_inizio, orario_fine, note=""):
        self.nome = nome
        self.day = day
        self.orario_inizio = orario_inizio
        self.orario_fine = orario_fine
        self.note = note

    def get_absolute_url(self):
        return f'{self.nome}: {self.orario_inizio} - {self.orario_fine}'


class EventCalendar(HTMLCalendar):
    def __init__(self, events=None):
        super(EventCalendar, self).__init__()
        self.events = events or []

    def formatday(self, day, weekday, events):
        events_from_day = [event for event in events if event.day.day == day]
        events_html = "<ul>"
        for event in events_from_day:
            events_html += f"<li>{event.get_absolute_url()}</li><br>"
        events_html += "</ul>"

        if day == 0:
            return '<td class="noday">&nbsp;</td>'
        else:
            return f'<td class="{self.cssclasses[weekday]}">{day}{events_html}</td>'

    def formatweek(self, theweek, events):
        s = ''.join(self.formatday(d, wd, events) for (d, wd) in theweek)
        return f'<tr class="tr">{s}</tr>'

    def formatmonth(self, theyear, themonth, withyear=True):
        events = [event for event in self.events if event.day.month == themonth]

        v = []
        v.append('<table border="0" cellpadding="0" cellspacing="0" class="month">')
        v.append(self.formatmonthname(theyear, themonth, withyear=withyear))
        v.append(self.formatweekheader())
        for week in self.monthdays2calendar(theyear, themonth):
            v.append(self.formatweek(week, events))
        v.append('</table>')
        return ''.join(v)


# Esempio di utilizzo
if __name__ == "__main__":
    eventi = load_data('appuntamenti.pkl')
    calendar = EventCalendar(events=eventi)
    today = date.today()

    html_calendar = calendar.formatmonth(today.year, today.month)
    print(html_calendar)
