from Backend.pickle_manager import save_data, load_data

class Fattura:
    def __init__(self, id, numero, data, importo):
        self.id = id
        self.numero = numero
        self.data = data
        self.importo = importo

    @classmethod
    def all(cls):
        return load_data('fatture')

    @classmethod
    def get(cls, id):
        fatture = cls.all()
        for fattura in fatture:
            if fattura.id == id:
                return fattura
        return None

    def save(self):
        fatture = self.all()
        fatture = [f for f in fatture if f.id != self.id]
        fatture.append(self)
        save_data(fatture, 'fatture')

    def delete(self):
        fatture = self.all()
        fatture = [f for f in fatture if f.id != self.id]
        save_data(fatture, 'fatture')
