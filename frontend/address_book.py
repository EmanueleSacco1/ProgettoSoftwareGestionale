import tkinter
import tkinter.messagebox as tkmb
import customtkinter as ctk

# Import backend logic
from backend import address_book as db_rubrica

# Import the base class using a relative import
from .page_base import PageBase

class PaginaRubrica(PageBase):
    """
    Page for managing the Address Book.
    
    This page features a classic list/detail layout, allowing users
    to search and select contacts from a list on the left and
    edit their details in a form on the right.
    """
    def __init__(self, master):
        """
        Initialize the Address Book page.
        
        Args:
            master: The parent widget (main_content_frame from App).
        """
        super().__init__(master, fg_color="transparent")

        # --- Layout ---
        # Column 0 = List, Column 1 = Form
        self.grid_columnconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=2) 
        self.grid_rowconfigure(1, weight=1)
        
        self.id_contatto_selezionato = None # Tracks which contact is being edited
        self.font_bold = ctk.CTkFont(weight="bold")

        # --- Column 0: List and Search ---
        frame_lista = ctk.CTkFrame(self)
        frame_lista.grid(row=0, column=0, rowspan=2, padx=(20, 10), pady=20, sticky="nsew")
        frame_lista.grid_rowconfigure(2, weight=1)
        frame_lista.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame_lista, text="Contatti", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=(10,5), sticky="w")
        
        # Search Bar
        self.entry_ricerca = ctk.CTkEntry(frame_lista, placeholder_text="Cerca per nome, P.IVA...")
        self.entry_ricerca.grid(row=1, column=0, padx=(10,5), pady=(5,10), sticky="ew")
        # Bind the <Return> key (Enter) to the search function
        self.entry_ricerca.bind("<Return>", lambda e: self.aggiorna_lista_contatti())
        
        btn_cerca = ctk.CTkButton(frame_lista, text="Cerca", width=60, command=self.aggiorna_lista_contatti)
        btn_cerca.grid(row=1, column=1, padx=(5,10), pady=(5,10), sticky="ew")

        # Scrollable Frame for contact list
        self.frame_scroll_contatti = ctk.CTkScrollableFrame(frame_lista, fg_color="transparent")
        self.frame_scroll_contatti.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # --- Column 1: Detail Form ---
        frame_form = ctk.CTkFrame(self)
        frame_form.grid(row=1, column=1, padx=(10, 20), pady=(0, 20), sticky="nsew")
        frame_form.grid_columnconfigure(1, weight=1)
        
        # Form Title and "New" button
        frame_titolo_form = ctk.CTkFrame(self, fg_color="transparent")
        frame_titolo_form.grid(row=0, column=1, padx=(10,20), pady=(20,0), sticky="ew")
        
        self.lbl_titolo_form = ctk.CTkLabel(frame_titolo_form, text="Dettaglio Contatto", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_titolo_form.pack(side="left", padx=10)
        
        btn_pulisci = ctk.CTkButton(frame_titolo_form, text="Nuovo Contatto", width=100, command=self.pulisci_form)
        btn_pulisci.pack(side="right", padx=10)

        # --- Form Grid ---
        row = 0
        ctk.CTkLabel(frame_form, text="Tipo").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        self.seg_tipo = ctk.CTkSegmentedButton(frame_form, values=["Cliente", "Fornitore"])
        self.seg_tipo.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        
        row += 1
        ctk.CTkLabel(frame_form, text="Nome*").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        self.entry_nome = ctk.CTkEntry(frame_form)
        self.entry_nome.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        
        row += 1
        ctk.CTkLabel(frame_form, text="Azienda").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        self.entry_azienda = ctk.CTkEntry(frame_form)
        self.entry_azienda.grid(row=row, column=1, padx=10, pady=10, sticky="ew")

        row += 1
        ctk.CTkLabel(frame_form, text="P.IVA / CF").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        self.entry_piva = ctk.CTkEntry(frame_form)
        self.entry_piva.grid(row=row, column=1, padx=10, pady=10, sticky="ew")

        row += 1
        ctk.CTkLabel(frame_form, text="Email").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        self.entry_email = ctk.CTkEntry(frame_form)
        self.entry_email.grid(row=row, column=1, padx=10, pady=10, sticky="ew")

        row += 1
        ctk.CTkLabel(frame_form, text="Telefono").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        self.entry_tel = ctk.CTkEntry(frame_form)
        self.entry_tel.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        
        row += 1
        ctk.CTkLabel(frame_form, text="Indirizzo").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        self.entry_indirizzo = ctk.CTkEntry(frame_form)
        self.entry_indirizzo.grid(row=row, column=1, padx=10, pady=10, sticky="ew")

        row += 1
        ctk.CTkLabel(frame_form, text="Note").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        self.entry_note = ctk.CTkEntry(frame_form)
        self.entry_note.grid(row=row, column=1, padx=10, pady=10, sticky="ew")

        # --- Form Action Buttons ---
        frame_azioni_form = ctk.CTkFrame(frame_form, fg_color="transparent")
        frame_azioni_form.grid(row=row+1, column=0, columnspan=2, padx=10, pady=20, sticky="ew")
        frame_azioni_form.grid_columnconfigure(0, weight=1)
        frame_azioni_form.grid_columnconfigure(1, weight=1)
        
        btn_salva = ctk.CTkButton(frame_azioni_form, text="Salva Modifiche", command=self.salva_contatto)
        btn_salva.grid(row=0, column=0, padx=5, pady=10, sticky="ew")

        btn_elimina = ctk.CTkButton(frame_azioni_form, text="Elimina Contatto", fg_color="#D32F2F", hover_color="#B71C1C",
                                     command=self.elimina_contatto)
        btn_elimina.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        # Load initial data when page is created
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