from Backend.pickle_manager import save_data, load_data

class Agenda:
    def __init__(self, id, data, descrizione):
        self.id = id
        self.data = data
        self.descrizione = descrizione

    @classmethod
    def all(cls):
        return load_data('agenda')

    @classmethod
    def get(cls, id):
        eventi = cls.all()
        for evento in eventi:
            if evento.id == id:
                return evento
        return None

    def save(self):
        eventi = self.all()
        eventi = [e for e in eventi if e.id != self.id]
        eventi.append(self)
        save_data(eventi, 'agenda')

    def delete(self):
        eventi = self.all()
        eventi = [e for e in eventi if e.id != self.id]
        save_data(eventi, 'agenda')
