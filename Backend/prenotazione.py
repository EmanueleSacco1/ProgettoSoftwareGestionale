from Backend.pickle_manager import save_data, load_data

class Prenotazione:
    def __init__(self, id, data, cliente):
        self.id = id
        self.data = data
        self.cliente = cliente

    @classmethod
    def all(cls):
        return load_data('prenotazioni')

    @classmethod
    def get(cls, id):
        prenotazioni = cls.all()
        for prenotazione in prenotazioni:
            if prenotazione.id == id:
                return prenotazione
        return None

    def save(self):
        prenotazioni = self.all()
        prenotazioni = [p for p in prenotazioni if p.id != self.id]
        prenotazioni.append(self)
        save_data(prenotazioni, 'prenotazioni')

    def delete(self):
        prenotazioni = self.all()
        prenotazioni = [p for p in prenotazioni if p.id != self.id]
        save_data(prenotazioni, 'prenotazioni')
