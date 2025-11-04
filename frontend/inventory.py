import tkinter
import tkinter.messagebox as tkmb
import customtkinter as ctk
from decimal import Decimal, InvalidOperation

# Import backend logic
from backend import inventory as db_magazzino

# Import the base class
from .page_base import PageBase

class PaginaMagazzino(PageBase):
    """
    Page for managing the Warehouse/Inventory.
    
    This page uses a list/detail layout, similar to the Rubrica page,
    to manage inventory items (articoli) and their stock.
    """
    def __init__(self, master):
        """
        Initialize the Warehouse page.
        
        Args:
            master: The parent widget (main_content_frame from App).
        """
        super().__init__(master, fg_color="transparent")
        
        # Remove the "Under Construction" label from PageBase
        for widget in self.winfo_children():
            widget.destroy()

        # --- Layout ---
        # Column 0 = List, Column 1 = Form
        self.grid_columnconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=2) 
        self.grid_rowconfigure(1, weight=1)
        
        self.id_articolo_selezionato = None # Tracks which item is being edited
        self.font_bold = ctk.CTkFont(weight="bold")

        # --- Column 0: List and Search ---
        frame_lista = ctk.CTkFrame(self)
        frame_lista.grid(row=0, column=0, rowspan=2, padx=(20, 10), pady=20, sticky="nsew")
        frame_lista.grid_rowconfigure(2, weight=1)
        frame_lista.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame_lista, text="Articoli in Magazzino", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=(10,5), sticky="w")
        
        # Search Bar
        self.entry_ricerca = ctk.CTkEntry(frame_lista, placeholder_text="Cerca per nome, codice...")
        self.entry_ricerca.grid(row=1, column=0, padx=(10,5), pady=(5,10), sticky="ew")
        self.entry_ricerca.bind("<Return>", lambda e: self.aggiorna_lista_articoli())
        
        btn_cerca = ctk.CTkButton(frame_lista, text="Cerca", width=60, command=self.aggiorna_lista_articoli)
        btn_cerca.grid(row=1, column=1, padx=(5,10), pady=(5,10), sticky="ew")

        # Scrollable Frame for item list
        self.frame_scroll_articoli = ctk.CTkScrollableFrame(frame_lista, fg_color="transparent")
        self.frame_scroll_articoli.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # --- Column 1: Detail Form ---
        frame_form = ctk.CTkFrame(self)
        frame_form.grid(row=1, column=1, padx=(10, 20), pady=(0, 20), sticky="nsew")
        frame_form.grid_columnconfigure(1, weight=1)
        
        # Form Title and "New" button
        frame_titolo_form = ctk.CTkFrame(self, fg_color="transparent")
        frame_titolo_form.grid(row=0, column=1, padx=(10,20), pady=(20,0), sticky="ew")
        
        self.lbl_titolo_form = ctk.CTkLabel(frame_titolo_form, text="Dettaglio Articolo", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_titolo_form.pack(side="left", padx=10)
        
        btn_pulisci = ctk.CTkButton(frame_titolo_form, text="Nuovo Articolo", width=100, command=self.pulisci_form)
        btn_pulisci.pack(side="right", padx=10)

        # --- Form Grid ---
        row = 0
        ctk.CTkLabel(frame_form, text="Nome*").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        self.entry_nome = ctk.CTkEntry(frame_form)
        self.entry_nome.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        
        row += 1
        ctk.CTkLabel(frame_form, text="Codice (SKU)").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        self.entry_codice = ctk.CTkEntry(frame_form)
        self.entry_codice.grid(row=row, column=1, padx=10, pady=10, sticky="ew")

        row += 1
        ctk.CTkLabel(frame_form, text="Descrizione").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        self.entry_desc = ctk.CTkEntry(frame_form)
        self.entry_desc.grid(row=row, column=1, padx=10, pady=10, sticky="ew")

        row += 1
        ctk.CTkLabel(frame_form, text="Prezzo Acquisto (€)").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        self.entry_prezzo = ctk.CTkEntry(frame_form)
        self.entry_prezzo.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        
        row += 1
        ctk.CTkLabel(frame_form, text="Quantità in Stock").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        self.entry_stock = ctk.CTkEntry(frame_form)
        self.entry_stock.grid(row=row, column=1, padx=10, pady=10, sticky="w")

        # --- Form Action Buttons ---
        frame_azioni_form = ctk.CTkFrame(frame_form, fg_color="transparent")
        frame_azioni_form.grid(row=row+1, column=0, columnspan=2, padx=10, pady=20, sticky="ew")
        frame_azioni_form.grid_columnconfigure(0, weight=1)
        frame_azioni_form.grid_columnconfigure(1, weight=1)
        
        btn_salva = ctk.CTkButton(frame_azioni_form, text="Salva Modifiche", command=self.salva_articolo)
        btn_salva.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        btn_elimina = ctk.CTkButton(frame_azioni_form, text="Elimina Articolo", fg_color="#D32F2F", hover_color="#B71C1C",
                                     command=self.elimina_articolo)
        btn_elimina.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        btn_stock = ctk.CTkButton(frame_azioni_form, text="Carico/Scarico Stock Manuale...", command=self.modifica_stock_popup)
        btn_stock.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # Load initial data when page is created
        self.on_show()

    def on_show(self):
        """
        Overrides PageBase.on_show().
        Called by the main App when this page is raised.
        Refreshes the item list and clears the form.
        """
        print("Refreshing Magazzino page...")
        self.aggiorna_lista_articoli()
        self.pulisci_form()

    def aggiorna_lista_articoli(self, event=None):
        """
        Loads (or reloads) the item list on the left,
        applying the search filter if one is provided.
        """
        query = self.entry_ricerca.get()
        
        # Clear the previous list
        for widget in self.frame_scroll_articoli.winfo_children():
            widget.destroy()
            
        try:
            # Get items from the backend
            if query:
                articoli = db_magazzino.search_articoli(query)
            else:
                articoli = db_magazzino.get_all_articoli()
                
            if not articoli:
                ctk.CTkLabel(self.frame_scroll_articoli, text="Nessun articolo trovato.").pack(padx=10, pady=10)
                return

            # Populate the list with clickable frames
            for i, art in enumerate(sorted(articoli, key=lambda x: x.get('nome', ''))):
                nome = art.get('nome', 'Senza Nome')
                stock = art.get('qta_in_stock', 0)
                
                frame_art = ctk.CTkFrame(self.frame_scroll_articoli, fg_color="transparent", cursor="hand2")
                frame_art.pack(fill="x", padx=5, pady=(2,0))
                
                lbl_nome = ctk.CTkLabel(frame_art, text=f"{nome} (Cod: {art.get('codice', 'N/A')})", font=self.font_bold, anchor="w")
                lbl_nome.pack(fill="x")
                lbl_stock = ctk.CTkLabel(frame_art, text=f"Stock: {stock}", anchor="w")
                lbl_stock.pack(fill="x")
                
                # Bind the click event to show details
                frame_art.bind("<Button-1>", lambda e, a=art: self.mostra_dettagli_articolo(a))
                lbl_nome.bind("<Button-1>", lambda e, a=art: self.mostra_dettagli_articolo(a))
                lbl_stock.bind("<Button-1>", lambda e, a=art: self.mostra_dettagli_articolo(a))
                
                if i < len(articoli) - 1:
                    ctk.CTkFrame(self.frame_scroll_articoli, height=1, fg_color="gray").pack(fill="x", padx=5, pady=3)

        except Exception as e:
            tkmb.showerror("Errore", f"Impossibile caricare gli articoli:\n{e}")

    def mostra_dettagli_articolo(self, articolo):
        """
        Populates the form on the right with the details
        of the clicked item.
        
        Args:
            articolo (dict): The item dictionary to display.
        """
        self.pulisci_form()
        
        # Store the ID of the item being edited
        self.id_articolo_selezionato = articolo.get('id')
        self.lbl_titolo_form.configure(text=f"Modifica: {articolo.get('nome')}")
        
        # Populate all entry fields
        self.entry_nome.insert(0, articolo.get('nome', ''))
        self.entry_codice.insert(0, articolo.get('codice', ''))
        self.entry_desc.insert(0, articolo.get('descrizione', ''))
        self.entry_prezzo.insert(0, str(articolo.get('prezzo_acquisto', '0.0')))
        self.entry_stock.insert(0, str(articolo.get('qta_in_stock', '0.0')))
        # Stock is read-only here, must be changed via popup
        self.entry_stock.configure(state="disabled")

    def pulisci_form(self, event=None):
        """
        Clears the form on the right and resets it to "New Item" mode.
        """
        self.id_articolo_selezionato = None
        self.lbl_titolo_form.configure(text="Nuovo Articolo")
        
        # Clear all fields
        self.entry_nome.delete(0, "end")
        self.entry_codice.delete(0, "end")
        self.entry_desc.delete(0, "end")
        self.entry_prezzo.delete(0, "end")
        self.entry_stock.configure(state="normal") # Enable for creation
        self.entry_stock.delete(0, "end")
        
        # Set defaults
        self.entry_prezzo.insert(0, "0.0")
        self.entry_stock.insert(0, "0.0")
        
        self.entry_nome.focus() # Set focus to the first field

    def salva_articolo(self):
        """
        Collects data from the form and calls the backend to
        either create a new item or update an existing one.
        """
        nome = self.entry_nome.get()
        if not nome:
            tkmb.showwarning("Dati Mancanti", "Il campo 'Nome' è obbligatorio.")
            return

        try:
            dati = {
                'nome': nome,
                'codice': self.entry_codice.get(),
                'descrizione': self.entry_desc.get(),
                'prezzo_acquisto': float(self.entry_prezzo.get() or "0.0"),
            }

            if self.id_articolo_selezionato:
                # --- Update Existing ---
                # Stock is *not* updated from this save button
                db_magazzino.update_articolo(self.id_articolo_selezionato, dati)
                msg = "Articolo aggiornato!"
            else:
                # --- Create New ---
                # Stock *is* set on creation
                dati['qta_in_stock'] = float(self.entry_stock.get() or "0.0")
                db_magazzino.create_articolo(dati)
                msg = "Articolo creato!"
            
            tkmb.showinfo("Successo", msg)
            self.pulisci_form()
            self.aggiorna_lista_articoli() # Refresh the list

        except (ValueError, InvalidOperation):
            tkmb.showerror("Errore", "Prezzo e Quantità devono essere numeri validi.")
        except Exception as e:
            tkmb.showerror("Errore", f"Impossibile salvare l'articolo:\n{e}")

    def elimina_articolo(self):
        """
        Deletes the item currently loaded in the form.
        """
        if not self.id_articolo_selezionato:
            tkmb.showwarning("Nessuna Selezione", "Nessun articolo selezionato.")
            return

        nome = self.entry_nome.get()
        # Ask for confirmation
        if not tkmb.askyesno("Conferma Eliminazione", 
                             f"Sei sicuro di voler eliminare '{nome}'?"):
            return
            
        try:
            # TODO: Add check if item is used in any invoices
            db_magazzino.delete_articolo(self.id_articolo_selezionato)
            tkmb.showinfo("Successo", "Articolo eliminato.")
            self.pulisci_form()
            self.aggiorna_lista_articoli() # Refresh the list
        except Exception as e:
            tkmb.showerror("Errore", f"Impossibile eliminare l'articolo:\n{e}")

    def modifica_stock_popup(self):
        """
        Opens a simple dialog to manually adjust stock (add or remove).
        """
        if not self.id_articolo_selezionato:
            tkmb.showwarning("Nessuna Selezione", "Seleziona un articolo prima di modificare lo stock.")
            return
            
        dialog = ctk.CTkInputDialog(text="Inserisci la quantità da aggiungere (es. 10) o rimuovere (es. -3):",
                                     title="Carico/Scarico Stock")
        
        input_qta = dialog.get_input()
        
        if input_qta:
            try:
                quantita = Decimal(input_qta)
                success, msg = db_magazzino.update_stock(self.id_articolo_selezionato, quantita)
                
                if success:
                    tkmb.showinfo("Successo", msg)
                    # Refresh list and form
                    self.aggiorna_lista_articoli()
                    articolo = db_magazzino.find_articolo_by_id(self.id_articolo_selezionato)
                    self.mostra_dettagli_articolo(articolo)
                else:
                    tkmb.showwarning("Errore", msg)
                    
            except InvalidOperation:
                tkmb.showerror("Errore", "Quantità non valida.")