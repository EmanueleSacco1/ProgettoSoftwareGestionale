import tkinter.messagebox as tkmb
import customtkinter as ctk
from backend import address_book as db_rubrica
from .page_base import PageBase

class PaginaRubrica(PageBase):
    """Gestione della Rubrica (lista + dettaglio contatto)."""
    
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        # Layout principale
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)

        self.id_contatto_selezionato = None
        self.font_bold = ctk.CTkFont(weight="bold")

        # --- Colonna sinistra: Lista contatti ---
        frame_lista = ctk.CTkFrame(self, corner_radius=10)
        frame_lista.grid(row=0, column=0, rowspan=2, padx=(20, 10), pady=20, sticky="nsew")
        frame_lista.grid_rowconfigure(2, weight=1)
        frame_lista.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame_lista, text="Rubrica Contatti", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=15, pady=(15, 10), sticky="w"
        )

        # Barra di ricerca
        search_frame = ctk.CTkFrame(frame_lista, fg_color="transparent")
        search_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        search_frame.grid_columnconfigure(0, weight=1)

        self.entry_ricerca = ctk.CTkEntry(search_frame, placeholder_text="Cerca per nome o P.IVA...")
        self.entry_ricerca.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.entry_ricerca.bind("<Return>", lambda e: self.aggiorna_lista_contatti())

        btn_cerca = ctk.CTkButton(search_frame, text="Cerca", width=80, command=self.aggiorna_lista_contatti)
        btn_cerca.grid(row=0, column=1)

        # Elenco contatti
        self.frame_scroll_contatti = ctk.CTkScrollableFrame(frame_lista, fg_color="transparent")
        self.frame_scroll_contatti.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

        # --- Colonna destra: Form dettagli ---
        frame_titolo_form = ctk.CTkFrame(self, fg_color="transparent")
        frame_titolo_form.grid(row=0, column=1, padx=(10, 20), pady=(20, 0), sticky="ew")

        self.lbl_titolo_form = ctk.CTkLabel(
            frame_titolo_form, text="Dettaglio Contatto", font=ctk.CTkFont(size=18, weight="bold")
        )
        self.lbl_titolo_form.pack(side="left", padx=10)

        btn_nuovo = ctk.CTkButton(frame_titolo_form, text="Nuovo Contatto", width=120, command=self.pulisci_form)
        btn_nuovo.pack(side="right", padx=10)

        frame_form = ctk.CTkFrame(self, corner_radius=10)
        frame_form.grid(row=1, column=1, padx=(10, 20), pady=(0, 20), sticky="nsew")
        frame_form.grid_columnconfigure(1, weight=1)

        labels = [
            ("Tipo", None),
            ("Nome*", "entry_nome"),
            ("Azienda", "entry_azienda"),
            ("P.IVA / CF", "entry_piva"),
            ("Email", "entry_email"),
            ("Telefono", "entry_tel"),
            ("Indirizzo", "entry_indirizzo"),
            ("Note", "entry_note"),
        ]

        self.seg_tipo = ctk.CTkSegmentedButton(frame_form, values=["Cliente", "Fornitore"])
        self.seg_tipo.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        row = 1
        for label, attr in labels[1:]:
            ctk.CTkLabel(frame_form, text=label).grid(row=row, column=0, padx=10, pady=8, sticky="w")
            entry = ctk.CTkEntry(frame_form)
            entry.grid(row=row, column=1, padx=10, pady=8, sticky="ew")
            setattr(self, attr, entry)
            row += 1

        # Pulsanti azione
        frame_btn = ctk.CTkFrame(frame_form, fg_color="transparent")
        frame_btn.grid(row=row, column=0, columnspan=2, padx=10, pady=20, sticky="ew")
        frame_btn.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(frame_btn, text="Salva Modifiche", command=self.salva_contatto).grid(row=0, column=0, padx=5, sticky="ew")
        ctk.CTkButton(frame_btn, text="Elimina Contatto", fg_color="#D32F2F", hover_color="#B71C1C",
                      command=self.elimina_contatto).grid(row=0, column=1, padx=5, sticky="ew")

        self.on_show()

    def on_show(self):
        """
        Overrides PageBase.on_show().
        Called by the main App when this page is raised.
        Refreshes the contact list and clears the form.
        """
        print("Refreshing Rubrica page...")
        self.aggiorna_lista_contatti()
        self.pulisci_form()

    def aggiorna_lista_contatti(self, event=None):
        """
        Loads (or reloads) the contact list on the left,
        applying the search filter if one is provided.
        """
        query = self.entry_ricerca.get()
        
        # Clear the previous list
        for widget in self.frame_scroll_contatti.winfo_children():
            widget.destroy()
            
        try:
            # Get contacts from the backend
            if query:
                contatti = db_rubrica.search_contacts(query)
            else:
                contatti = db_rubrica.get_all_contacts()
                
            if not contatti:
                ctk.CTkLabel(self.frame_scroll_contatti, text="Nessun contatto trovato.").pack(padx=10, pady=10)
                return

            # Populate the list with clickable frames
            for i, contact in enumerate(sorted(contatti, key=lambda x: x.get('name', ''))):
                nome = contact.get('name', 'Senza Nome')
                azienda = contact.get('company', 'Privato')
                
                # Create a frame that acts as a button
                frame_contatto = ctk.CTkFrame(self.frame_scroll_contatti, fg_color="transparent", cursor="hand2")
                frame_contatto.pack(fill="x", padx=5, pady=(2,0))
                
                lbl_nome = ctk.CTkLabel(frame_contatto, text=nome, font=self.font_bold, anchor="w")
                lbl_nome.pack(fill="x")
                lbl_azienda = ctk.CTkLabel(frame_contatto, text=f"{azienda} ({contact.get('type')})", anchor="w")
                lbl_azienda.pack(fill="x")
                
                # Bind the click event to show details
                frame_contatto.bind("<Button-1>", lambda e, c=contact: self.mostra_dettagli_contatto(c))
                lbl_nome.bind("<Button-1>", lambda e, c=contact: self.mostra_dettagli_contatto(c))
                lbl_azienda.bind("<Button-1>", lambda e, c=contact: self.mostra_dettagli_contatto(c))
                
                # Add a separator
                if i < len(contatti) - 1:
                    ctk.CTkFrame(self.frame_scroll_contatti, height=1, fg_color="gray").pack(fill="x", padx=5, pady=3)

        except Exception as e:
            tkmb.showerror("Errore", f"Impossibile caricare i contatti:\n{e}")

    def mostra_dettagli_contatto(self, contact):
        """
        Populates the form on the right with the details
        of the clicked contact.
        
        Args:
            contact (dict): The contact dictionary to display.
        """
        self.pulisci_form() # Clear form first
        
        # Store the ID of the contact being edited
        self.id_contatto_selezionato = contact.get('id')
        self.lbl_titolo_form.configure(text=f"Modifica: {contact.get('name')}")
        
        # Populate all entry fields
        self.seg_tipo.set(contact.get('type', 'Cliente'))
        self.entry_nome.insert(0, contact.get('name', ''))
        self.entry_azienda.insert(0, contact.get('company', ''))
        self.entry_piva.insert(0, contact.get('vat_id', ''))
        self.entry_email.insert(0, contact.get('email', ''))
        self.entry_tel.insert(0, contact.get('phone', ''))
        self.entry_indirizzo.insert(0, contact.get('address', ''))
        self.entry_note.insert(0, contact.get('notes', ''))

    def pulisci_form(self, event=None):
        """
        Clears the form on the right and resets it to "New Contact" mode.
        """
        self.id_contatto_selezionato = None
        self.lbl_titolo_form.configure(text="Nuovo Contatto")
        
        self.seg_tipo.set("Cliente")
        self.entry_nome.delete(0, "end")
        self.entry_azienda.delete(0, "end")
        self.entry_piva.delete(0, "end")
        self.entry_email.delete(0, "end")
        self.entry_tel.delete(0, "end")
        self.entry_indirizzo.delete(0, "end")
        self.entry_note.delete(0, "end")
        
        self.entry_nome.focus() # Set focus to the first field

    def salva_contatto(self):
        """
        Collects data from the form and calls the backend to
        either create a new contact or update an existing one.
        """
        # Collect data from widgets
        dati = {
            'type': self.seg_tipo.get(),
            'name': self.entry_nome.get(),
            'company': self.entry_azienda.get(),
            'vat_id': self.entry_piva.get(),
            'email': self.entry_email.get(),
            'phone': self.entry_tel.get(),
            'address': self.entry_indirizzo.get(),
            'notes': self.entry_note.get()
        }

        if not dati['name']:
            tkmb.showwarning("Dati Mancanti", "Il campo 'Nome' è obbligatorio.")
            return

        try:
            if self.id_contatto_selezionato:
                # --- Update Existing ---
                db_rubrica.update_contact(self.id_contatto_selezionato, dati)
                msg = "Contatto aggiornato!"
            else:
                # --- Create New ---
                db_rubrica.create_contact(dati)
                msg = "Contatto creato!"
            
            tkmb.showinfo("Successo", msg)
            self.pulisci_form()
            self.aggiorna_lista_contatti() # Refresh the list

        except Exception as e:
            tkmb.showerror("Errore", f"Impossibile salvare il contatto:\n{e}")

    def elimina_contatto(self):
        """
        Deletes the contact currently loaded in the form.
        """
        if not self.id_contatto_selezionato:
            tkmb.showwarning("Nessuna Selezione", "Nessun contatto selezionato da eliminare.")
            return

        nome = self.entry_nome.get()
        # Ask for confirmation
        if not tkmb.askyesno("Conferma Eliminazione", 
                             f"Sei sicuro di voler eliminare '{nome}'?\nL'azione è irreversibile."):
            return
            
        try:
            db_rubrica.delete_contact(self.id_contatto_selezionato)
            tkmb.showinfo("Successo", "Contatto eliminato.")
            self.pulisci_form()
            self.aggiorna_lista_contatti() # Refresh the list
        except Exception as e:
            tkmb.showerror("Errore", f"Impossibile eliminare il contatto:\n{e}")