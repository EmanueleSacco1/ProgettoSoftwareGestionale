from Backend.pickle_manager import save_data, load_data

class Prodotto:
    def __init__(self, id, nome, prezzo):
        self.id = id
        self.nome = nome
        self.prezzo = prezzo

    @classmethod
    def all(cls):
        return load_data('prodotti')

    @classmethod
    def get(cls, id):
        prodotti = cls.all()
        for prodotto in prodotti:
            if prodotto.id == id:
                return prodotto
        return None

    def save(self):
        prodotti = self.all()
        prodotti = [p for p in prodotti if p.id != self.id]
        prodotti.append(self)
        save_data(prodotti, 'prodotti')

    def delete(self):
        prodotti = self.all()
        prodotti = [p for p in prodotti if p.id != self.id]
        save_data(prodotti, 'prodotti')
