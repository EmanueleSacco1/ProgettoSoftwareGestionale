from Backend.prenotazione import Prenotazione
from Backend.prodotto import Prodotto
from Backend.fattura import Fattura
from Backend.agenda import Agenda
from Backend.tariffa import Tariffa


def crea_prenotazione():
    id = int(input("ID prenotazione: "))
    data = input("Data prenotazione (YYYY-MM-DD): ")
    cliente = input("Nome cliente: ")
    prenotazione = Prenotazione(id, data, cliente)
    prenotazione.save()
    print("Prenotazione salvata con successo!")


def visualizza_prenotazioni():
    prenotazioni = Prenotazione.all()
    if not prenotazioni:
        print("Nessuna prenotazione trovata.")
        return
    for prenotazione in prenotazioni:
        print(f"ID: {prenotazione.id}, Data: {prenotazione.data}, Cliente: {prenotazione.cliente}")


def crea_fattura():
    id = int(input("ID fattura: "))
    numero = input("Numero fattura: ")
    data = input("Data fattura (YYYY-MM-DD): ")
    importo = float(input("Importo: "))
    fattura = Fattura(id, numero, data, importo)
    fattura.save()
    print("Fattura salvata con successo!")


def visualizza_fatture():
    fatture = Fattura.all()
    if not fatture:
        print("Nessuna fattura trovata.")
        return
    for fattura in fatture:
        print(f"ID: {fattura.id}, Numero: {fattura.numero}, Data: {fattura.data}, Importo: {fattura.importo}")


def crea_evento_agenda():
    id = int(input("ID evento: "))
    data = input("Data evento (YYYY-MM-DD): ")
    descrizione = input("Descrizione: ")
    evento = Agenda(id, data, descrizione)
    evento.save()
    print("Evento salvato con successo!")


def visualizza_eventi_agenda():
    eventi = Agenda.all()
    if not eventi:
        print("Nessun evento trovato.")
        return
    for evento in eventi:
        print(f"ID: {evento.id}, Data: {evento.data}, Descrizione: {evento.descrizione}")


def crea_tariffa():
    id = int(input("ID tariffa: "))
    descrizione = input("Descrizione: ")
    importo = float(input("Importo: "))
    tariffa = Tariffa(id, descrizione, importo)
    tariffa.save()
    print("Tariffa salvata con successo!")


def visualizza_tariffe():
    tariffe = Tariffa.all()
    if not tariffe:
        print("Nessuna tariffa trovata.")
        return
    for tariffa in tariffe:
        print(f"ID: {tariffa.id}, Descrizione: {tariffa.descrizione}, Importo: {tariffa.importo}")


def crea_prodotto():
    id = int(input("ID prodotto: "))
    nome = input("Nome prodotto: ")
    prezzo = float(input("Prezzo prodotto: "))
    prodotto = Prodotto(id, nome, prezzo)
    prodotto.save()
    print("Prodotto salvato con successo!")


def visualizza_prodotti():
    prodotti = Prodotto.all()
    if not prodotti:
        print("Nessun prodotto trovato.")
        return
    for prodotto in prodotti:
        print(f"ID: {prodotto.id}, Nome: {prodotto.nome}, Prezzo: {prodotto.prezzo}")


def elimina_prodotto():
    id = int(input("ID del prodotto da eliminare: "))
    prodotto = Prodotto.get(id)
    if prodotto:
        prodotto.delete()
        print("Prodotto eliminato.")
    else:
        print("Prodotto non trovato.")


def main():
    while True:
        print("\nGestione Applicazione")
        print("1. Crea Prenotazione")
        print("2. Visualizza Prenotazioni")
        print("3. Crea Fattura")
        print("4. Visualizza Fatture")
        print("5. Crea Evento Agenda")
        print("6. Visualizza Eventi Agenda")
        print("7. Crea Tariffa")
        print("8. Visualizza Tariffe")
        print("9. Crea Prodotto")
        print("10. Visualizza Prodotti")
        print("11. Elimina Prodotto")
        print("12. Esci")

        scelta = input("Seleziona un'opzione: ")

        if scelta == "1":
            crea_prenotazione()
        elif scelta == "2":
            visualizza_prenotazioni()
        elif scelta == "3":
            crea_fattura()
        elif scelta == "4":
            visualizza_fatture()
        elif scelta == "5":
            crea_evento_agenda()
        elif scelta == "6":
            visualizza_eventi_agenda()
        elif scelta == "7":
            crea_tariffa()
        elif scelta == "8":
            visualizza_tariffe()
        elif scelta == "9":
            crea_prodotto()
        elif scelta == "10":
            visualizza_prodotti()
        elif scelta == "11":
            elimina_prodotto()
        elif scelta == "12":
            print("Uscita...")
            break
        else:
            print("Opzione non valida, riprova.")


if __name__ == "__main__":
    main()
