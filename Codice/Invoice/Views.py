import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from datetime import date

# Directory per il salvataggio dei PDF
PDF_ROOT = 'path/to/save/pdf/'  # Modifica questo percorso in base alle tue esigenze
os.makedirs(PDF_ROOT, exist_ok=True)


# Classe per la fattura
@dataclass
class Fattura:
    numero: int
    nome: str
    cognome: str
    nome_ditta: str
    citta: str
    via: str
    num_civico: int
    cap: int
    partita_iva: str
    data: date
    descrizione_pag: str
    banca: str


# Classe per la tariffa
@dataclass
class TariffaFatt:
    descrizione_prod: str
    quantita: int
    prezzo: float
    fattura: Fattura


class ControllerFattura:

    @staticmethod
    def generatePDF(fattura: Fattura, tariffe: list):
        # Creazione del canvas per il PDF
        c = canvas.Canvas(os.path.join(PDF_ROOT, f'fattura_{fattura.numero}.pdf'))
        width, height = A4
        c.translate(inch / 1.75, inch * 1.3)

        # Intestazione
        c.setFont("Helvetica", 10)
        intestazione = c.beginText(3.2 * inch, 9.2 * inch)
        intestazione.textLine('Mario Rossi')
        intestazione.textLine('Via Brecce Bianche 12, 60131 Ancona (AN)')
        intestazione.textLine('Codice Fiscale: MRORSS12321321312 - P.IVA: 123456789')
        intestazione.textLine('Telefono: +39 0712204708')
        intestazione.textLine('PEC: mariorossi@univpm.it')
        c.drawText(intestazione)
        c.line(0 * inch, 8.5 * inch, 7.1 * inch, 8.5 * inch)

        # Destinatario
        c.setFont("Helvetica-Bold", 10)
        c.drawString(0 * inch, 8.2 * inch, 'Destinatario:')
        c.setFont("Helvetica", 10)
        destinatario = c.beginText(1.1 * inch, 8.2 * inch)
        destinatario.textLine(f'{fattura.nome} {fattura.cognome}')
        destinatario.textLine(f'Via {fattura.via}, {fattura.num_civico} - {fattura.cap} {fattura.citta}')
        destinatario.textLine('Italia')
        destinatario.textLine(f'P.IVA: {fattura.partita_iva}')
        c.drawText(destinatario)

        # Dati fattura
        c.setFont("Helvetica-Bold", 10)
        dati = c.beginText(4.5 * inch, 8.2 * inch)
        dati.textLine('Fattura:')
        dati.textLine('Tipo di documento:')
        dati.textLine('Data Fattura:')
        c.drawText(dati)

        c.setFont("Helvetica", 10)
        dati1 = c.beginText(6 * inch, 8.2 * inch)
        dati1.textLine(str(fattura.numero))
        dati1.textLine('Fattura')
        dati1.textLine(str(fattura.data))
        c.drawText(dati1)

        # Dettagli pagamento
        c.line(0 * inch, 7.62 * inch, 7.1 * inch, 7.62 * inch)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(0 * inch, 7.48 * inch, 'Descrizione pagamento:')
        c.drawString(4 * inch, 7.48 * inch, 'Banca d\'appoggio:')
        c.setFont("Helvetica", 10)
        c.drawString(1.7 * inch, 7.48 * inch, fattura.descrizione_pag)
        c.drawString(5.3 * inch + 2, 7.48 * inch, fattura.banca)
        c.line(0 * inch, 7.42 * inch, 7.1 * inch, 7.42 * inch)

        # Tabella dettagli fattura
        c.setFont("Helvetica-Bold", 12)
        c.drawString(0.2 * inch, 7.2 * inch, 'Descrizione')
        c.line(0 * inch, 7.15 * inch, 7.1 * inch, 7.15 * inch)
        c.drawCentredString(4.5 * inch, 7.2 * inch, 'Quantita')
        c.drawCentredString(5.2 * inch, 7.2 * inch, 'Prezzo')
        c.drawCentredString(5.9 * inch, 7.2 * inch, 'IVA')
        c.drawCentredString(6.6 * inch, 7.2 * inch, 'Importo')

        # Dettagli tariffe
        c.setFont("Helvetica", 11)
        row_gap = 0.4  # gap tra le righe
        line_y = 6.9  # posizione della prima riga
        total = 0
        for tariffa in tariffe:
            if tariffa.fattura.numero == fattura.numero:
                c.drawString(0.2 * inch, line_y * inch, str(tariffa.descrizione_prod))
                c.drawCentredString(4.5 * inch, line_y * inch, str(tariffa.quantita))
                c.drawCentredString(5.2 * inch, line_y * inch, str(tariffa.prezzo))
                c.drawCentredString(5.9 * inch, line_y * inch, '0%')
                sub_total = tariffa.prezzo * tariffa.quantita
                c.drawCentredString(6.6 * inch, line_y * inch, str(round(sub_total, 2)))
                total += sub_total
                line_y -= row_gap

        # Totali
        c.line(0.01 * inch, line_y * inch, 7 * inch, line_y * inch)  # linea orizzontale totale
        row_gap = 0.2
        linea_impon = line_y - row_gap
        c.drawRightString(5.2 * inch, linea_impon * inch, 'Imponibile')
        c.drawRightString(7 * inch, linea_impon * inch, str(round(total, 2)))
        contributi = round(0.04 * total, 2)
        linea_contr = linea_impon - row_gap
        c.drawRightString(5.2 * inch, linea_contr * inch, 'Contributi (INPS) 4%')
        c.drawRightString(7 * inch, linea_contr * inch, str(contributi))
        iva = 0
        linea_iva = linea_contr - row_gap
        c.drawRightString(5.2 * inch, linea_iva * inch, f'IVA 0% di {total + contributi} (art.10 n.18 DPR 633/1972)')
        c.drawRightString(7 * inch, linea_iva * inch, str(iva))
        linea_tot = linea_iva - row_gap
        total_final = round(total + contributi + iva, 2)
        c.setFont("Helvetica-Bold", 11)
        c.drawRightString(5.2 * inch, linea_tot * inch, 'Totale EUR')
        c.drawRightString(7 * inch, linea_tot * inch, str(total_final))
        linea_bollo = linea_tot - 1.2 * row_gap
        c.setFont("Helvetica", 11)
        c.drawRightString(5.2 * inch, linea_bollo * inch, 'Fattura soggetta a bollo')
        c.drawRightString(7 * inch, linea_bollo * inch, '2.00')
        linea = linea_bollo - 0.1
        total_final += 2
        c.line(3.5 * inch, linea * inch, 7 * inch, linea * inch)
        linea_pag = linea - row_gap
        c.setFont("Helvetica-Bold", 11)
        c.drawRightString(5.2 * inch, linea_pag * inch, 'Da Pagare: (EUR)')
        c.drawRightString(7 * inch, linea_pag * inch, str(total_final))

        # Termini e condizioni
        linea_tc = linea_pag - 3 * row_gap
        c.drawString(0.1 * inch, linea_tc * inch, 'Termini e Condizioni')
        c.setFont("Helvetica", 11)
        c.drawString(0.1 * inch, (linea_tc - row_gap) * inch, 'Operazione es
