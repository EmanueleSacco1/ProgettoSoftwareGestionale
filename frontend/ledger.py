import tkinter
import tkinter.messagebox as tkmb
import customtkinter as ctk
from .page_base import PageBase
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
import os

# Import backend logic
from backend import ledger as db_ledger     # Renamed
from backend import tax as db_tasse
from backend import documents as db_docs
from backend import address_book as db_rubrica
from backend import persistence as db

class PaginaLedger(PageBase): # --- CLASSE RINOMINATA ---
    """
    Page for managing the Financial Ledger (Registro Movimenti) and Tax Estimates.
    
    This page uses a CTkTabview to separate the two main functions:
    1.  Ledger (Registro Movimenti): Logging income/expenses and exporting for the accountant.
    2.  Tax (Stima Tasse): Configuring tax rates and viewing estimations.
    """
    def __init__(self, master):
        """
        Initialize the Accounting (Ledger) page.
        
        Args:
            master: The parent widget (main_content_frame from App).
        """
        super().__init__(master, fg_color="transparent")
        
        # Configure layout
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self, text="Contabilità e Tasse", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Main TabView to separate Ledger and Tax
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=1, column=0, sticky="nsew")
        
        self.tab_primanota = self.tab_view.add("Registro Movimenti") # Renamed
        self.tab_tasse = self.tab_view.add("Stima Tasse")
        
        # Create the widgets for each tab
        self._crea_widgets_tab_registro(self.tab_primanota) # Renamed
        self._crea_widgets_tab_tasse(self.tab_tasse)

    def on_show(self):
        """
        Overrides PageBase.on_show().
        Called by the main App when this page is raised.
        Refreshes the financial ledger list and reloads tax rates.
        """
        print("Refreshing Contabilità page...")
        self._aggiorna_lista_movimenti()
        self._carica_aliquote() # Reload tax rates in case they changed

    # --- Registro Movimenti (Ledger) Tab ---

    def _crea_widgets_tab_registro(self, tab): # Renamed
        """
        Helper method to populate the 'Registro Movimenti' (Ledger) tab 
        with its widgets (buttons, scrollable list).
        
        Args:
            tab (CTkFrame): The parent tab frame.
        """
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        
        # Frame for action buttons
        frame_azioni = ctk.CTkFrame(tab, fg_color="transparent")
        frame_azioni.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        # --- Action Buttons ---
        ctk.CTkButton(frame_azioni, text="Registra Incasso (da Fattura)", command=self.apri_popup_registra_incasso).pack(side="left", padx=5)
        ctk.CTkButton(frame_azioni, text="Registra Uscita", command=lambda: self.apri_popup_movimento_manuale('Uscita')).pack(side="left", padx=5)
        ctk.CTkButton(frame_azioni, text="Registra Entrata", command=lambda: self.apri_popup_movimento_manuale('Entrata')).pack(side="left", padx=5)
        ctk.CTkButton(frame_azioni, text="Esporta per Commercialista", command=self.esporta_commercialista).pack(side="left", padx=5)
        ctk.CTkButton(frame_azioni, text="Grafico Annuale", command=self.genera_grafico_primanota).pack(side="left", padx=5)
        
        # --- Scrollable List for Transactions ---
        self.frame_scroll_movimenti = ctk.CTkScrollableFrame(tab)
        self.frame_scroll_movimenti.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        self.frame_scroll_movimenti.grid_columnconfigure(1, weight=1) # Configure column for description
        
    def _aggiorna_lista_movimenti(self):
        """Clears and repopulates the list of financial transactions (movements)."""
        for widget in self.frame_scroll_movimenti.winfo_children():
            widget.destroy()
            
        try:
            # Get movements for the last 90 days as a default view
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=90)
            movimenti = db_ledger.get_movimenti(start_date, end_date)
            
            ctk.CTkLabel(self.frame_scroll_movimenti, text=f"Movimenti degli ultimi 90 giorni (dal {start_date.isoformat()})",
                         font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, columnspan=4, sticky="w", padx=5, pady=5)
            
            if not movimenti:
                ctk.CTkLabel(self.frame_scroll_movimenti, text="Nessun movimento trovato.").grid(row=1, column=0, pady=10)
                return

            # --- Header Row ---
            header_frame = ctk.CTkFrame(self.frame_scroll_movimenti, fg_color="transparent")
            header_frame.grid(row=1, column=0, columnspan=4, sticky="ew", padx=5, pady=2)
            header_frame.grid_columnconfigure(0, minsize=100) # Date
            header_frame.grid_columnconfigure(1, weight=1)   # Description
            header_frame.grid_columnconfigure(2, minsize=100) # Amount
            header_frame.grid_columnconfigure(3, minsize=30)  # Delete btn
            ctk.CTkLabel(header_frame, text="Data", font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(header_frame, text="Descrizione", font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=0, column=1, sticky="w")
            ctk.CTkLabel(header_frame, text="Importo", font=ctk.CTkFont(weight="bold"), anchor="e").grid(row=0, column=2, sticky="e")
            # Separator
            ctk.CTkFrame(self.frame_scroll_movimenti, height=1, fg_color="gray").grid(row=2, column=0, columnspan=4, sticky="ew", padx=5, pady=(0, 5))

            # --- Transaction Rows ---
            for i, mov in enumerate(movimenti):
                row_frame = ctk.CTkFrame(self.frame_scroll_movimenti, fg_color="transparent")
                row_frame.grid(row=i+3, column=0, columnspan=4, sticky="ew", padx=5)
                row_frame.grid_columnconfigure(1, weight=1)
                row_frame.grid_columnconfigure(2, minsize=100)
                row_frame.grid_columnconfigure(3, minsize=30)

                # Set color and sign based on transaction type
                color = "green" if mov['type'] == 'Entrata' else "red"
                importo = mov['amount_totale'] if mov['type'] == 'Entrata' else -mov['amount_totale']
                
                ctk.CTkLabel(row_frame, text=mov['date'], width=100, anchor="w").grid(row=0, column=0, sticky="w")
                ctk.CTkLabel(row_frame, text=mov['description'], anchor="w").grid(row=0, column=1, sticky="ew", padx=10)
                ctk.CTkLabel(row_frame, text=f"{importo:.2f} €", text_color=color, anchor="e").grid(row=0, column=2, sticky="e")
                
                # Delete button for each transaction
                btn_del = ctk.CTkButton(row_frame, text="X", width=30, fg_color="#D32F2F", hover_color="#B71C1C",
                                        command=lambda id=mov['id']: self.elimina_movimento(id))
                btn_del.grid(row=0, column=3, padx=(5,0))
                
        except Exception as e:
            tkmb.showerror("Errore", f"Impossibile caricare i movimenti: {e}")

    def apri_popup_registra_incasso(self):
        """
        Opens a modal popup to select an unpaid invoice and mark it as paid.
        This function links the Documents module with the Ledger module.
        """
        
        popup = ctk.CTkToplevel(self)
        popup.title("Registra Incasso da Fattura")
        popup.geometry("500x250")
        
        ctk.CTkLabel(popup, text="Seleziona la fattura incassata:").pack(pady=10)
        
        try:
            # Find unpaid invoices
            invoices = [f for f in db_docs.get_all_documents(doc_type='invoice') if f['status'] in ['In sospeso', 'Scaduto']]
            clienti = {c['id']: c for c in db_rubrica.get_all_contacts()}
            
            # Create display strings and a map to get the invoice ID
            invoice_options = [f"{f['number']} - {clienti.get(f['client_id'], {'name': 'N/A'})['name']} ({f['total_da_pagare']:.2f} €)" for f in invoices]
            invoice_map = {f"{f['number']} - {clienti.get(f['client_id'], {'name': 'N/A'})['name']} ({f['total_da_pagare']:.2f} €)": f['id'] for f in invoices}

            if not invoice_options:
                tkmb.showerror("Errore", "Nessuna fattura da incassare trovata.", parent=popup)
                popup.destroy()
                return

            combo_invoices = ctk.CTkComboBox(popup, values=invoice_options, width=450)
            combo_invoices.pack(pady=5, padx=10)
        except Exception as e:
            tkmb.showerror("Errore", f"Impossibile caricare le fatture: {e}", parent=popup)
            popup.destroy()
            return

        ctk.CTkLabel(popup, text="Data Incasso (YYYY-MM-DD):").pack(pady=(10,0))
        entry_data = ctk.CTkEntry(popup, width=150)
        entry_data.insert(0, datetime.now().date().isoformat()) # Default to today
        entry_data.pack(pady=5)
        
        def salva_incasso():
            """Nested callback to save the invoice payment."""
            invoice_str = combo_invoices.get()
            data_incasso = entry_data.get()
            if not invoice_str or not data_incasso:
                tkmb.showwarning("Dati Mancanti", "Seleziona una fattura e inserisci una data.", parent=popup)
                return
            
            invoice_id = invoice_map[invoice_str]
            
            try:
                # Call backend to create ledger entry AND update invoice status
                success, msg = db_ledger.create_movimento_from_invoice(invoice_id, data_incasso)
                if success:
                    tkmb.showinfo("Successo", msg, parent=popup)
                    popup.destroy()
                    self.on_show() # Refresh lists
                else:
                    tkmb.showerror("Errore", msg, parent=popup)
            except Exception as e:
                tkmb.showerror("Errore", f"Impossibile salvare:\n{e}", parent=popup)

        ctk.CTkButton(popup, text="Registra Incasso", command=salva_incasso).pack(pady=20)
        
        popup.transient(self)
        popup.grab_set()
        self.wait_window(popup)

    def apri_popup_movimento_manuale(self, tipo):
        """
        Opens a modal popup to manually add an 'Entrata' (Income) 
        or 'Uscita' (Expense).
        
        Args:
            tipo (str): 'Entrata' or 'Uscita', to set the title and logic.
        """
        popup = ctk.CTkToplevel(self)
        popup.title(f"Registra {tipo} Manuale")
        popup.geometry("450x450")
        
        frame_grid = ctk.CTkFrame(popup, fg_color="transparent")
        frame_grid.pack(fill="both", expand=True, padx=10, pady=10)
        frame_grid.grid_columnconfigure(1, weight=1)
        
        # --- Form Fields ---
        row = 0
        ctk.CTkLabel(frame_grid, text="Data (YYYY-MM-DD):").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        entry_data = ctk.CTkEntry(frame_grid)
        entry_data.insert(0, datetime.now().date().isoformat())
        entry_data.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        
        row += 1
        ctk.CTkLabel(frame_grid, text="Descrizione:").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        entry_desc = ctk.CTkEntry(frame_grid)
        entry_desc.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        
        row += 1
        ctk.CTkLabel(frame_grid, text="Imponibile (Netto):").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        entry_netto = ctk.CTkEntry(frame_grid)
        entry_netto.insert(0, "0.0")
        entry_netto.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        
        row += 1
        ctk.CTkLabel(frame_grid, text="IVA:").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        entry_iva = ctk.CTkEntry(frame_grid)
        entry_iva.insert(0, "0.0")
        entry_iva.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        
        row += 1
        ctk.CTkLabel(frame_grid, text="Ritenuta:").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        entry_ritenuta = ctk.CTkEntry(frame_grid)
        entry_ritenuta.insert(0, "0.0")
        entry_ritenuta.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        
        row += 1
        ctk.CTkLabel(frame_grid, text="Note:").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        entry_note = ctk.CTkEntry(frame_grid)
        entry_note.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        
        row += 1
        lbl_totale = ctk.CTkLabel(frame_grid, text="Totale: 0.00 €", font=ctk.CTkFont(weight="bold"))
        lbl_totale.grid(row=row, column=1, padx=10, pady=10, sticky="e")
        
        def calcola_totale(*args):
            """
            Nested function to updates the total label live as the user types 
            in the financial fields.
            """
            try:
                netto = Decimal(entry_netto.get() or '0')
                iva = Decimal(entry_iva.get() or '0')
                ritenuta = Decimal(entry_ritenuta.get() or '0')
                totale = netto + iva - ritenuta
                lbl_totale.configure(text=f"Totale: {totale:.2f} €")
            except InvalidOperation:
                lbl_totale.configure(text="Totale: Errore")
        
        # Bind calculation to key release in the number fields
        entry_netto.bind("<KeyRelease>", calcola_totale)
        entry_iva.bind("<KeyRelease>", calcola_totale)
        entry_ritenuta.bind("<KeyRelease>", calcola_totale)
        
        def salva_movimento():
            """Nested callback to validate and save the manual transaction."""
            try:
                # Re-calculate totals for saving
                netto = Decimal(entry_netto.get() or '0')
                iva = Decimal(entry_iva.get() or '0')
                ritenuta = Decimal(entry_ritenuta.get() or '0')
                totale = netto + iva - ritenuta
                
                # Build data dictionary
                data = {
                    'date': entry_data.get(),
                    'type': tipo,
                    'description': entry_desc.get(),
                    'amount_netto': netto,
                    'amount_iva': iva,
                    'amount_ritenuta': ritenuta,
                    'amount_totale': totale,
                    'notes': entry_note.get()
                }
                
                if not data['description'] or not data['date']:
                    tkmb.showwarning("Dati Mancanti", "Data e Descrizione sono obbligatori.", parent=popup)
                    return
                
                # Call backend to save
                success, msg = db_ledger.create_movimento(data)
                
                if success:
                    tkmb.showinfo("Successo", msg, parent=popup)
                    popup.destroy()
                    self.on_show() # Refresh main list
                else:
                    tkmb.showerror("Errore", msg, parent=popup)
                    
            except Exception as e:
                tkmb.showerror("Errore", f"Dati non validi: {e}", parent=popup)
        
        ctk.CTkButton(frame_grid, text=f"Salva {tipo}", command=salva_movimento).grid(row=row+2, column=1, padx=10, pady=20, sticky="e")
        
        popup.transient(self)
        popup.grab_set()
        self.wait_window(popup)

    def elimina_movimento(self, movimento_id):
        """
        Deletes a financial transaction after confirmation.
        Warns the user about potential invoice status reverts.
        
        Args:
            movimento_id (str): The ID of the transaction to delete.
        """
        if not tkmb.askyesno("Conferma", "Vuoi eliminare questo movimento?\nSe è collegato a una fattura, lo stato della fattura verrà ripristinato."):
            return
        
        try:
            success, msg = db_ledger.delete_movimento(movimento_id)
            if success:
                tkmb.showinfo("Successo", msg)
                self.on_show() # Refresh the list
            else:
                tkmb.showerror("Errore", msg)
        except Exception as e:
            tkmb.showerror("Errore", f"Impossibile eliminare: {e}")

    def esporta_commercialista(self):
        """
        Handles the process of exporting the annual ledger for the accountant.
        Asks for the year and the save location/format.
        """
        year_dialog = ctk.CTkInputDialog(text="Inserisci l'anno per l'esportazione:", title="Esporta per Commercialista")
        year_str = year_dialog.get_input()
        
        if not year_str: return
        try:
            year = int(year_str)
        except ValueError:
            tkmb.showerror("Errore", "Anno non valido.")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Salva Esportazione",
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx"), ("CSV (Separatore ;)", "*.csv")],
            initialfile=f"esportazione_registro_{year}" # Updated filename
        )
        
        if not file_path: return
        
        fmt = 'csv' if file_path.endswith('.csv') else 'excel'
        
        try:
            # Call backend export function
            success, msg = db_ledger.export_per_commercialista(file_path, year, fmt)
            if success:
                tkmb.showinfo("Successo", f"Esportazione completata:\n{msg}")
                os.startfile(os.path.dirname(file_path)) # Open the folder
            else:
                tkmb.showerror("Errore", msg)
        except Exception as e:
            tkmb.showerror("Errore Critico", f"Esportazione fallita:\n{e}")

    def genera_grafico_primanota(self):
        """
        Generates and saves the annual income/expense chart.
        Asks for the year and attempts to open the resulting .png file.
        """
        year_dialog = ctk.CTkInputDialog(text="Inserisci l'anno per il grafico:", title="Grafico Annuale")
        year_str = year_dialog.get_input()
        
        if not year_str: return
        try:
            year = int(year_str)
        except ValueError:
            tkmb.showerror("Errore", "Anno non valido.")
            return

        try:
            # 1. Get stats from backend
            stats_df, msg = db_ledger.generate_monthly_stats(year)
            if stats_df.empty:
                tkmb.showwarning("Nessun Dato", msg)
                return
            
            # 2. Plot the stats
            filename = f"statistiche_movimenti_{year}.png" # Updated filename
            success, msg_plot = db_ledger.plot_monthly_stats(stats_df, filename)
            
            if success:
                tkmb.showinfo("Successo", f"Grafico generato con successo:\n{msg_plot}")
                os.startfile(os.path.abspath(filename)) # Open the image
            else:
                tkmb.showerror("Errore Grafico", msg_plot)
                
        except Exception as e:
            tkmb.showerror("Errore Critico", f"Generazione grafico fallita:\n{e}")

    # --- Tax Estimation Tab ---
    
    def _crea_widgets_tab_tasse(self, tab):
        """
        Helper method to populate the 'Stima Tasse' (Tax Estimation) tab
        with its widgets.
        
        Args:
            tab (CTkFrame): The parent tab frame.
        """
        tab.grid_columnconfigure(0, weight=1)
        
        # --- Configuration Frame (for rates) ---
        frame_config = ctk.CTkFrame(tab)
        frame_config.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        frame_config.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(frame_config, text="Configurazione Aliquote Stimate", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=(10,5))
        
        frame_inps = ctk.CTkFrame(frame_config, fg_color="transparent")
        frame_inps.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        frame_inps.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(frame_inps, text="Aliquota INPS (%)", width=150, anchor="w").grid(row=0, column=0)
        self.entry_inps = ctk.CTkEntry(frame_inps)
        self.entry_inps.grid(row=0, column=1, sticky="ew")
        
        frame_irpef = ctk.CTkFrame(frame_config, fg_color="transparent")
        frame_irpef.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        frame_irpef.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(frame_irpef, text="Aliquota IRPEF Media (%)", width=150, anchor="w").grid(row=0, column=0)
        self.entry_irpef = ctk.CTkEntry(frame_irpef)
        self.entry_irpef.grid(row=0, column=1, sticky="ew")
        
        ctk.CTkButton(frame_config, text="Salva Aliquote", command=self.salva_aliquote).grid(row=3, column=1, padx=10, pady=10, sticky="e")
        
        # --- Estimation Frame (for quarterly buttons) ---
        frame_stima = ctk.CTkFrame(tab)
        frame_stima.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        frame_stima.grid_columnconfigure(0, weight=1)
        frame_stima.grid_columnconfigure(1, weight=1)
        frame_stima.grid_columnconfigure(2, weight=1)
        frame_stima.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(frame_stima, text="Calcola Stima per Anno Corrente:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=4, padx=10, pady=10)
        ctk.CTkButton(frame_stima, text="Trimestre 1 (Q1)", command=lambda: self.visualizza_stima(1)).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(frame_stima, text="Trimestre 2 (Q2)", command=lambda: self.visualizza_stima(2)).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(frame_stima, text="Trimestre 3 (Q3)", command=lambda: self.visualizza_stima(3)).grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(frame_stima, text="Trimestre 4 (Q4)", command=lambda: self.visualizza_stima(4)).grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        
        # Load initial values into entry fields
        self._carica_aliquote()

    def _carica_aliquote(self):
        """Loads the saved tax rates from the settings file into the entry fields."""
        settings = db.load_settings()
        tax_config = settings.get('tax_config', {})
        self.entry_inps.delete(0, "end")
        self.entry_inps.insert(0, str(tax_config.get('inps_perc', '26.07')))
        self.entry_irpef.delete(0, "end")
        self.entry_irpef.insert(0, str(tax_config.get('irpef_perc', '23.0')))

    def salva_aliquote(self):
        """Saves the user-defined tax rates from the entry fields to the settings file."""
        try:
            inps = float(self.entry_inps.get())
            irpef = float(self.entry_irpef.get())
            
            settings = db.load_settings()
            settings['tax_config'] = {'inps_perc': inps, 'irpef_perc': irpef}
            db.save_settings(settings)
            
            tkmb.showinfo("Successo", "Aliquote stimate salvate.")
        except Exception as e:
            tkmb.showerror("Errore", f"Valore non valido: {e}")

    def visualizza_stima(self, quarter):
        """
        Calculates and displays the tax estimation for a given quarter 
        in a new Toplevel popup window.
        
        Args:
            quarter (int): The quarter (1-4) to calculate for.
        """
        try:
            year = datetime.now().year
            # Call backend to get all estimation data
            risultato, msg = db_tasse.get_stima_completa(year, quarter)
            
            if not risultato:
                tkmb.showwarning("Errore Stima", msg)
                return

            # --- Format the results into a string for display ---
            msg_popup = f"--- STIMA PERIODO: {risultato['periodo']} (Anno {year}) ---\n\n"
            msg_popup += "*** ATTENZIONE: SOLO A SCOPO INFORMATIVO. ***\n\n"
            msg_popup += "--- Liquidazione IVA (Stima Trimestrale) ---\n"
            msg_popup += f"  IVA a Debito: {risultato['iva_debito']:.2f} €\n"
            msg_popup += f"  IVA a Credito: {risultato['iva_credito']:.2f} €\n"
            msg_popup += "  ---------------------------------------\n"
            msg_popup += f"  IVA da Versare (Stima): {risultato['iva_da_versare']:.2f} €\n\n"
            
            msg_popup += "--- Stima Contributi e Tasse (Proiezione Annuale YTD) ---\n"
            msg_popup += f"  (Aliquote usate: INPS {risultato['tax_config']['inps_perc']}%, IRPEF {risultato['tax_config']['irpef_perc']}%)\n"
            msg_popup += f"\n  Imponibile (Incassato Netto YTD): {risultato['imponibile_cassa']:.2f} €\n"
            msg_popup += "  ---------------------------------------\n"
            msg_popup += f"  Stima Contributi INPS: {risultato['contributi_inps']:.2f} €\n"
            msg_popup += f"  Imponibile IRPEF (Stima): {risultato['imponibile_irpef']:.2f} €\n"
            msg_popup += f"  Stima IRPEF (Lorda): {risultato['stima_irpef']:.2f} €\n"
            
            # Show in a Toplevel window with a read-only Textbox
            # This is better than a messagebox as it allows copy-pasting.
            popup = ctk.CTkToplevel(self)
            popup.title(f"Stima Tasse {risultato['periodo']}")
            popup.geometry("600x450")
            
            txt = ctk.CTkTextbox(popup, font=ctk.CTkFont(family="Monospace", size=13))
            txt.pack(fill="both", expand=True, padx=10, pady=10)
            txt.insert("1.0", msg_popup)
            txt.configure(state="disabled") # Make it read-only
            
            popup.transient(self)
            popup.grab_set()
            
        except Exception as e:
            tkmb.showerror("Errore", f"Errore imprevisto: {e}")