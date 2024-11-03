from Backend.pickle_manager import save_data, load_data

class Tariffa:
    def __init__(self, id, descrizione, importo):
        self.id = id
        self.descrizione = descrizione
        self.importo = importo

    @classmethod
    def all(cls):
        return load_data('tariffe')

    @classmethod
    def get(cls, id):
        tariffe = cls.all()
        for tariffa in tariffe:
            if tariffa.id == id:
                return tariffa
        return None

    def save(self):
        tariffe = self.all()
        tariffe = [t for t in tariffe if t.id != self.id]
        tariffe.append(self)
        save_data(tariffe, 'tariffe')

    def delete(self):
        tariffe = self.all()
        tariffe = [t for t in tariffe if t.id != self.id]
        save_data(tariffe, 'tariffe')
