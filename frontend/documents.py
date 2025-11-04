import tkinter
import tkinter.messagebox as tkmb
import customtkinter as ctk
from decimal import Decimal, InvalidOperation
import os

# Import backend logic
from backend import documents as db_docs
from backend import address_book as db_rubrica
from backend import inventory as db_magazzino

# Import the base class using a relative import
from .page_base import PageBase

class PaginaDocumenti(PageBase):
    """
    Page for managing Quotes and Invoices.
    
    This page uses a main CTkTabview to separate the two document types.
    It contains logic for creating, listing, and exporting documents.
    """
    def __init__(self, master):
        """
        Initialize the Documents page.
        
        Args:
            master: The parent widget (main_content_frame from App).
        """
        super().__init__(master)

        # Remove the "Under Construction" label from PageBase
        for widget in self.winfo_children():
            widget.destroy()
        
        # Configure layout
        self.pack(fill="both", expand=True, padx=20, pady=20)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self, text="Gestione Documenti", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=1, column=0, sticky="nsew")
        
        self.tab_preventivi = self.tab_view.add("Preventivi")
        self.tab_fatture = self.tab_view.add("Fatture")
        
        # Keep track of the currently selected document
        self.selected_quote_id = None
        self.selected_invoice_id = None
        
        # Create the widgets for each tab
        self._crea_widgets_tab_documenti(self.tab_preventivi, "quote")
        self._crea_widgets_tab_documenti(self.tab_fatture, "invoice")

    def on_show(self):
        """
        Overrides PageBase.on_show().
        Called by the main App when this page is raised.
        Refreshes both document lists.
        """
        print("Refreshing Documenti page...")
        self.aggiorna_lista_documenti("quote")
        self.aggiorna_lista_documenti("invoice")

    def _crea_widgets_tab_documenti(self, tab, doc_type):
        """
        Populates a given tab (Preventivi or Fatture) with its
        necessary widgets (buttons, scrollable list).
        
        Args:
            tab (CTkFrame): The parent tab frame.
            doc_type (str): 'quote' or 'invoice'.
        """
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        
        frame_azioni = ctk.CTkFrame(tab, fg_color="transparent")
        frame_azioni.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # --- Action Buttons ---
        btn_crea = ctk.CTkButton(frame_azioni, 
                                 text=f"Crea Nuov{'o Preventivo' if doc_type == 'quote' else 'a Fattura'}",
                                 command=lambda dt=doc_type: self.apri_popup_documento(doc_type=dt))
        btn_crea.pack(side="left", padx=5)

        if doc_type == "invoice":
            btn_converti = ctk.CTkButton(frame_azioni, text="Crea Fattura da Preventivo",
                                         command=self.apri_popup_conversione)
            btn_converti.pack(side="left", padx=5)
            
            btn_stato = ctk.CTkButton(frame_azioni, text="Aggiorna Stato Pagamento",
                                      command=self.apri_popup_aggiorna_stato)
            btn_stato.pack(side="left", padx=5)

        btn_esporta = ctk.CTkButton(frame_azioni, text="Esporta PDF Selezionato",
                                    command=lambda dt=doc_type: self.esporta_pdf_selezionato(dt))
        btn_esporta.pack(side="left", padx=5)
        
        # --- Scrollable List ---
        frame_scroll = ctk.CTkScrollableFrame(tab)
        frame_scroll.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Store references to the scrollable frames and their labels
        if doc_type == "quote":
            self.frame_scroll_preventivi = frame_scroll
            self.labels_preventivi = {}
        else:
            self.frame_scroll_fatture = frame_scroll
            self.labels_fatture = {}

    def aggiorna_lista_documenti(self, doc_type):
        """
        Refreshes the list of documents (quotes or invoices) in the
        specified tab's scrollable frame.
        
        Args:
            doc_type (str): 'quote' or 'invoice'.
        """
        if doc_type == "quote":
            frame_scroll = self.frame_scroll_preventivi
            self.labels_preventivi = {}
            self.selected_quote_id = None
        else:
            frame_scroll = self.frame_scroll_fatture
            self.labels_fatture = {}
            self.selected_invoice_id = None
        
        for widget in frame_scroll.winfo_children():
            widget.destroy()
            
        try:
            documenti = db_docs.get_all_documents(doc_type=doc_type)
            # Load client data once for efficiency
            clienti = {c['id']: c for c in db_rubrica.get_all_contacts()}
            
            if not documenti:
                ctk.CTkLabel(frame_scroll, text=f"Nessun{'a' if doc_type == 'invoice' else 'o'} {'Fattura' if doc_type == 'invoice' else 'Preventivo'} trovat{'a' if doc_type == 'invoice' else 'o'}.").pack(pady=10)
                return

            for doc in sorted(documenti, key=lambda x: x['date'], reverse=True):
                cliente = clienti.get(doc['client_id'], {'name': 'CLIENTE ELIMINATO'})
                
                # Determine the total to display
                total = doc.get('total_da_pagare', doc.get('total', 0))
                
                testo = f"[{doc['date']}] {doc['number']} - {cliente['name']} - {total:.2f} € ({doc['status']})"
                
                # Create a clickable label for each document
                lbl = ctk.CTkLabel(frame_scroll, text=testo, anchor="w", cursor="hand2")
                lbl.pack(fill="x", padx=5, pady=3)
                lbl.bind("<Button-1>", lambda e, dt=doc_type, doc_id=doc['id']: self.seleziona_documento(dt, doc_id))
                
                # Store the label reference
                if doc_type == "quote":
                    self.labels_preventivi[doc['id']] = lbl
                else:
                    self.labels_fatture[doc['id']] = lbl
                    
        except Exception as e:
            tkmb.showerror("Errore", f"Impossibile caricare i documenti: {e}")

    def seleziona_documento(self, doc_type, doc_id):
        """
        Handles the click event on a document label.
        Highlights the selected document.
        
        Args:
            doc_type (str): 'quote' or 'invoice'.
            doc_id (str): The ID of the clicked document.
        """
        if doc_type == "quote":
            self.selected_quote_id = doc_id
            labels_dict = self.labels_preventivi
        else:
            self.selected_invoice_id = doc_id
            labels_dict = self.labels_fatture
            
        # Reset all labels to default color
        for lbl in labels_dict.values():
            lbl.configure(fg_color="transparent")
            
        # Highlight the selected label
        if doc_id in labels_dict:
            labels_dict[doc_id].configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])

    def esporta_pdf_selezionato(self, doc_type):
        """
        Exports the currently selected document to PDF.
        
        Args:
            doc_type (str): 'quote' or 'invoice' to determine which ID to use.
        """
        doc_id = self.selected_quote_id if doc_type == "quote" else self.selected_invoice_id
        
        if not doc_id:
            tkmb.showwarning("Nessuna Selezione", "Seleziona un documento dalla lista prima di esportare.")
            return

        try:
            print(f"Generazione PDF per {doc_id}...")
            success, msg = db_docs.export_to_pdf(doc_id)
            if success:
                tkmb.showinfo("Successo", f"PDF generato con successo:\n{os.path.abspath(msg)}")
                os.startfile(os.path.dirname(msg)) # Open the folder
            else:
                tkmb.showerror("Errore PDF", f"Impossibile generare il PDF:\n{msg}")
        except Exception as e:
            tkmb.showerror("Errore Critico", f"Errore imprevisto durante l'esportazione PDF:\n{e}")

    # --- Popup Windows for Actions ---
    
    def apri_popup_documento(self, doc_type, quote_data=None):
        """
        Opens a Toplevel window to create a new Quote or Invoice.
        
        Args:
            doc_type (str): 'quote' or 'invoice'.
            quote_data (dict, optional): If provided, pre-fills the form
                                         (used for quote-to-invoice conversion).
        """
        popup = ctk.CTkToplevel(self)
        title = "Nuovo Preventivo" if doc_type == "quote" else "Nuova Fattura"
        if quote_data:
            title = f"Converti Preventivo {quote_data['number']}"
        popup.title(title)
        popup.geometry("600x650")

        popup.grid_columnconfigure(1, weight=1)
        
        # --- Client Selection ---
        row = 0
        ctk.CTkLabel(popup, text="Cliente*").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        
        try:
            clienti = db_rubrica.get_all_contacts()
            # Create a display-friendly list: "Name (Company)"
            clienti_options = [f"{c['name']} ({c.get('company', 'N/A')})" for c in clienti if c.get('type') == 'Cliente']
            # Map the display string back to the client ID
            clienti_map = {f"{c['name']} ({c.get('company', 'N/A')})": c['id'] for c in clienti if c.get('type') == 'Cliente'}
            
            if not clienti_options:
                tkmb.showerror("Errore", "Nessun 'Cliente' trovato in rubrica.", parent=popup)
                popup.destroy()
                return

            combo_clienti = ctk.CTkComboBox(popup, values=clienti_options, width=400)
            combo_clienti.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
            
            if quote_data:
                # Pre-select client from quote
                client = db_rubrica.find_contact_by_id(quote_data['client_id'])
                if client:
                    client_str = f"{client['name']} ({client.get('company', 'N/A')})"
                    combo_clienti.set(client_str)
                combo_clienti.configure(state="disabled") # Don't allow changing client on conversion

        except Exception as e:
            tkmb.showerror("Errore", f"Impossibile caricare i clienti: {e}", parent=popup)
            popup.destroy()
            return
            
        # --- Due Date (Invoices only) ---
        if doc_type == "invoice":
            row += 1
            ctk.CTkLabel(popup, text="Scadenza (YYYY-MM-DD)*").grid(row=row, column=0, padx=10, pady=10, sticky="w")
            entry_scadenza = ctk.CTkEntry(popup)
            entry_scadenza.grid(row=row, column=1, padx=10, pady=10, sticky="w")

        # --- Line Items ---
        row += 1
        ctk.CTkLabel(popup, text="Voci Documento", font=ctk.CTkFont(weight="bold")).grid(row=row, column=0, columnspan=2, padx=10, pady=(15,5), sticky="w")
        
        frame_voci = ctk.CTkScrollableFrame(popup, height=200)
        frame_voci.grid(row=row+1, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        
        line_items = [] # This list will hold all item data dicts

        def aggiungi_voce(voce=None):
            """
            Adds a new line item row to the scrollable frame.
            If 'voce' is provided, pre-fills it (for quote conversion).
            """
            item_frame = ctk.CTkFrame(frame_voci, fg_color="transparent")
            item_frame.pack(fill="x", pady=2)
            
            entry_desc = ctk.CTkEntry(item_frame, placeholder_text="Descrizione", width=250)
            entry_desc.pack(side="left", padx=5)
            
            entry_qty = ctk.CTkEntry(item_frame, width=50)
            entry_qty.pack(side="left", padx=5)
            
            entry_prezzo = ctk.CTkEntry(item_frame, width=80, placeholder_text="Prezzo Unit.")
            entry_prezzo.pack(side="left", padx=5)
            
            btn_del = ctk.CTkButton(item_frame, text="X", width=30, fg_color="#D32F2F", hover_color="#B71C1C")
            btn_del.pack(side="left", padx=5)
            
            linked_item_id = None # Store the warehouse item ID
            
            if voce:
                # Pre-fill from quote_data
                entry_desc.insert(0, voce.get('description', ''))
                entry_qty.insert(0, str(voce.get('qty', '1')))
                entry_prezzo.insert(0, str(voce.get('unit_price', '0')))
                linked_item_id = voce.get('articolo_id')
                # Disable fields if converting
                entry_desc.configure(state="disabled")
                entry_qty.configure(state="disabled")
                entry_prezzo.configure(state="disabled")
                btn_del.configure(state="disabled")
            else:
                entry_qty.insert(0, "1")

            # Store references to the widgets and data
            item_data = {'frame': item_frame, 'desc': entry_desc, 'qty': entry_qty, 'prezzo': entry_prezzo, 'articolo_id': linked_item_id}
            
            # Add command *after* creating item_data
            btn_del.configure(command=lambda d=item_data: rimuovi_voce(d))
            line_items.append(item_data)

        def rimuovi_voce(item_data):
            """Removes a line item from the list and destroys its frame."""
            item_data['frame'].destroy()
            line_items.remove(item_data)

        if quote_data:
            # Pre-fill all items from the quote
            for item in quote_data['items']:
                aggiungi_voce(item)
        else:
            # Add one blank row
            aggiungi_voce()
            
        # Add "Add Row" button only if not converting
        if not quote_data:
            btn_add_voce = ctk.CTkButton(popup, text="+ Aggiungi Voce", command=aggiungi_voce)
            btn_add_voce.grid(row=row+2, column=1, padx=10, pady=5, sticky="w")

        # --- Financial Fields ---
        row += 3
        frame_fin = ctk.CTkFrame(popup, fg_color="transparent")
        frame_fin.grid(row=row, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        frame_fin.grid_columnconfigure(1, weight=1)
        frame_fin.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(frame_fin, text="Sconto (%)").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        entry_sconto = ctk.CTkEntry(frame_fin, width=80)
        entry_sconto.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        entry_sconto.insert(0, str(quote_data.get('discount_perc', '0')))
        
        ctk.CTkLabel(frame_fin, text="IVA (%)").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        entry_iva = ctk.CTkEntry(frame_fin, width=80)
        entry_iva.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        entry_iva.insert(0, str(quote_data.get('vat_perc', '22')))
        
        # Ritenuta (Invoices only)
        if doc_type == "invoice":
            ctk.CTkLabel(frame_fin, text="Ritenuta (%)").grid(row=1, column=0, padx=5, pady=5, sticky="w")
            entry_ritenuta = ctk.CTkEntry(frame_fin, width=80)
            entry_ritenuta.grid(row=1, column=1, padx=5, pady=5, sticky="w")
            entry_ritenuta.insert(0, "0") # Ritenuta is always 0 on quotes

        # --- Notes ---
        row += 1
        ctk.CTkLabel(popup, text="Note").grid(row=row, column=0, padx=10, pady=5, sticky="w")
        entry_note = ctk.CTkEntry(popup)
        entry_note.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        if quote_data:
            entry_note.insert(0, quote_data.get('notes', ''))

        # --- Save Button ---
        def salva_documento():
            try:
                # 1. Get Client ID
                client_id = clienti_map[combo_clienti.get()]
                
                # 2. Collect Line Items
                items_data = []
                for item_row in line_items:
                    items_data.append({
                        'description': item_row['desc'].get(),
                        'qty': Decimal(item_row['qty'].get()),
                        'unit_price': Decimal(item_row['prezzo'].get()),
                        'articolo_id': item_row['articolo_id']
                    })
                if not items_data:
                    tkmb.showwarning("Dati Mancanti", "Aggiungere almeno una voce.", parent=popup)
                    return
                    
                # 3. Collect Financials
                dati_fin = {
                    'discount_perc': Decimal(entry_sconto.get() or '0'),
                    'vat_perc': Decimal(entry_iva.get() or '22'),
                    'notes': entry_note.get()
                }

                # 4. Call correct backend function
                if doc_type == 'invoice':
                    dati_fin['ritenuta_perc'] = Decimal(entry_ritenuta.get() or '0')
                    dati_fin['due_date'] = entry_scadenza.get()
                    if not dati_fin['due_date']:
                         tkmb.showwarning("Dati Mancanti", "La data di scadenza è obbligatoria.", parent=popup)
                         return
                         
                    if quote_data:
                        # This is a conversion
                        success, result = db_docs.convert_quote_to_invoice(
                            quote_id=quote_data['id'],
                            due_date=dati_fin['due_date'],
                            ritenuta_perc=dati_fin['ritenuta_perc']
                        )
                        if not success: raise Exception(result)
                    else:
                        # This is a new manual invoice
                        db_docs.create_invoice(
                            client_id=client_id, project_id=None, # TODO: add project link
                            items=items_data, **dati_fin
                        )
                
                else: # doc_type == 'quote'
                    db_docs.create_quote(
                        client_id=client_id, project_id=None, # TODO: add project link
                        items=items_data, **dati_fin
                    )
                
                tkmb.showinfo("Successo", f"{title} salvat{'a' if doc_type == 'invoice' else 'o'}.", parent=popup)
                popup.destroy()
                self.on_show() # Refresh lists

            except InvalidOperation:
                tkmb.showerror("Errore Formato", "Controlla che tutti i campi (Q.tà, Prezzo, %, ...) siano numeri validi.", parent=popup)
            except Exception as e:
                tkmb.showerror("Errore Salvataggio", f"Impossibile salvare:\n{e}", parent=popup)

        row += 1
        ctk.CTkButton(popup, text=f"Salva {'Fattura' if doc_type == 'invoice' else 'Preventivo'}", command=salva_documento).grid(row=row, column=1, padx=10, pady=20, sticky="e")
        
        popup.transient(self)
        popup.grab_set()
        self.wait_window(popup)

    def apri_popup_conversione(self):
        """Opens a popup to select a Quote to convert into an Invoice."""
        
        # 1. Create selection popup
        popup = ctk.CTkToplevel(self)
        popup.title("Converti Preventivo in Fattura")
        popup.geometry("500x200")
        
        ctk.CTkLabel(popup, text="Seleziona il preventivo da convertire:").pack(pady=10)
        
        try:
            # Filter for quotes that are not already 'Fatturato'
            quotes = [q for q in db_docs.get_all_documents(doc_type='quote') if q['status'] != 'Fatturato']
            clienti = {c['id']: c for c in db_rubrica.get_all_contacts()}
            
            quote_options = [f"{q['number']} - {clienti.get(q['client_id'], {'name': 'N/A'})['name']}" for q in quotes]
            quote_map = {f"{q['number']} - {clienti.get(q['client_id'], {'name': 'N/A'})['name']}": q for q in quotes}

            if not quote_options:
                tkmb.showerror("Errore", "Nessun preventivo da convertire trovato.", parent=popup)
                popup.destroy()
                return

            combo_quotes = ctk.CTkComboBox(popup, values=quote_options, width=400)
            combo_quotes.pack(pady=5, padx=10)
        except Exception as e:
            tkmb.showerror("Errore", f"Impossibile caricare i preventivi: {e}", parent=popup)
            popup.destroy()
            return

        def on_next():
            """Called when user selects a quote and clicks Next."""
            quote_str = combo_quotes.get()
            if not quote_str:
                tkmb.showwarning("Selezione Mancante", "Seleziona un preventivo.", parent=popup)
                return
            
            quote_data = quote_map[quote_str]
            popup.destroy() # Close this popup
            # Open the main document popup, pre-filled
            self.apri_popup_documento(doc_type="invoice", quote_data=quote_data)

        ctk.CTkButton(popup, text="Avanti", command=on_next).pack(pady=20)
        
        popup.transient(self)
        popup.grab_set()
        self.wait_window(popup)
    
    def apri_popup_aggiorna_stato(self):
        """Opens a popup to change the status of the selected invoice."""
        if not self.selected_invoice_id:
            tkmb.showwarning("Nessuna Selezione", "Seleziona una fattura dalla lista.")
            return

        invoice = db_docs.find_document_by_id(self.selected_invoice_id)
        
        popup = ctk.CTkToplevel(self)
        popup.title(f"Aggiorna Stato: {invoice['number']}")
        popup.geometry("300x150")
        
        ctk.CTkLabel(popup, text="Seleziona nuovo stato:").pack(pady=10)
        
        combo_stati = ctk.CTkComboBox(popup, values=db_docs.VALID_INVOICE_STATUS)
        combo_stati.set(invoice['status'])
        combo_stati.pack(pady=5, padx=20, fill="x")
        
        def salva_stato():
            new_status = combo_stati.get()
            try:
                db_docs.update_document_status(self.selected_invoice_id, new_status)
                tkmb.showinfo("Successo", "Stato aggiornato.", parent=popup)
                popup.destroy()
                self.aggiorna_lista_documenti("invoice")
            except Exception as e:
                tkmb.showerror("Errore", f"Impossibile aggiornare lo stato:\n{e}", parent=popup)
        
        ctk.CTkButton(popup, text="Salva Stato", command=salva_stato).pack(pady=15)
        
        popup.transient(self)
        popup.grab_set()
        self.wait_window(popup)