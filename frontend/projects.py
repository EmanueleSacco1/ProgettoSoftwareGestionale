import tkinter
import tkinter.messagebox as tkmb
import customtkinter as ctk
from tkinter import filedialog
import os
from datetime import datetime

# Import backend logic
from backend import projects as db_progetti
from backend import address_book as db_rubrica

# Import the base class using a relative import
from .page_base import PageBase

class PaginaProgetti(PageBase):
    """
    Page for managing Projects.
    
    This page uses a List/Detail layout. The left side shows a searchable
    list of all projects. The right side (detail view) uses a
    CTkTabview to separate a project's Dashboard, Phases, Activities, and Files.
    """
    def __init__(self, master):
        """
        Initialize the Projects page.
        
        Args:
            master: The parent widget (main_content_frame from App).
        """
        super().__init__(master, fg_color="transparent")

        # --- Layout Configuration ---
        # Column 0 = List, Column 1 = Detail
        self.grid_columnconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=2) # Detail view is wider
        self.grid_rowconfigure(1, weight=1)    # Detail view expands vertically
        
        self.progetto_selezionato = None # Tracks the currently loaded project object
        self.font_bold = ctk.CTkFont(weight="bold")

        # --- Column 0: List, Search, New Button ---
        frame_lista = ctk.CTkFrame(self)
        frame_lista.grid(row=0, column=0, rowspan=2, padx=(20, 10), pady=20, sticky="nsew")
        frame_lista.grid_rowconfigure(3, weight=1) # Make list scroll area expand
        frame_lista.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame_lista, text="Progetti", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=(10,5), sticky="w")
        
        # Search bar
        self.entry_ricerca = ctk.CTkEntry(frame_lista, placeholder_text="Cerca progetto...")
        self.entry_ricerca.grid(row=1, column=0, padx=(10,5), pady=(5,10), sticky="ew")
        self.entry_ricerca.bind("<Return>", lambda e: self.aggiorna_lista_progetti())
        
        btn_cerca = ctk.CTkButton(frame_lista, text="Cerca", width=60, command=self.aggiorna_lista_progetti)
        btn_cerca.grid(row=1, column=1, padx=(5,10), pady=(5,10), sticky="ew")

        btn_nuovo = ctk.CTkButton(frame_lista, text="Nuovo Progetto", command=self.crea_nuovo_progetto_popup)
        btn_nuovo.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        # Scrollable list for projects
        self.frame_scroll_progetti = ctk.CTkScrollableFrame(frame_lista, fg_color="transparent")
        self.frame_scroll_progetti.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # --- Column 1: Detail View (using TabView) ---
        self.frame_dettaglio = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_dettaglio.grid(row=0, column=1, rowspan=2, padx=(10, 20), pady=20, sticky="nsew")
        self.frame_dettaglio.grid_rowconfigure(1, weight=1)
        self.frame_dettaglio.grid_columnconfigure(0, weight=1)

        self.lbl_titolo_form = ctk.CTkLabel(self.frame_dettaglio, text="Seleziona un progetto", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_titolo_form.grid(row=0, column=0, padx=10, pady=(10,5), sticky="w")

        # TabView for project details
        self.tab_view = ctk.CTkTabview(self.frame_dettaglio, state="disabled") # Disabled until a project is selected
        self.tab_view.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Create tabs
        self.tab_dashboard = self.tab_view.add("Dashboard")
        self.tab_fasi = self.tab_view.add("Fasi")
        self.tab_attivita = self.tab_view.add("Attività")
        self.tab_file = self.tab_view.add("File")
        
        # Create the widgets inside each tab
        self._crea_widgets_dashboard(self.tab_dashboard)
        self._crea_widgets_fasi(self.tab_fasi)
        self._crea_widgets_attivita(self.tab_attivita)
        self._crea_widgets_file(self.tab_file)
        
        # Load initial list
        self.on_show()

    def on_show(self):
        """
        Overrides PageBase.on_show().
        Called by the main App when this page is raised.
        Refreshes the project list and clears the detail view.
        """
        print("Refreshing Progetti page...")
        self.aggiorna_lista_progetti()
        self._pulisci_dettagli()

    def _pulisci_dettagli(self):
        """Helper function to reset the detail view to its initial state."""
        self.progetto_selezionato = None
        self.lbl_titolo_form.configure(text="Seleziona un progetto")
        self.tab_view.configure(state="disabled") # Hide/disable the tab view

    def aggiorna_lista_progetti(self, event=None):
        """
        Loads (or reloads) the project list on the left,
        applying the search filter if one is provided.
        """
        query = self.entry_ricerca.get()
        
        # Clear previous list
        for widget in self.frame_scroll_progetti.winfo_children():
            widget.destroy()
            
        try:
            # TODO: Add a status filter dropdown (e.g., "Active", "Archived")
            all_progetti = db_progetti.get_all_projects()
            
            # Filter by search query
            if query:
                query_lower = query.lower()
                progetti = [p for p in all_progetti if query_lower in p['name'].lower()]
            else:
                progetti = all_progetti

            if not progetti:
                ctk.CTkLabel(self.frame_scroll_progetti, text="Nessun progetto trovato.").pack(padx=10, pady=10)
                return

            # Populate the list with clickable frames, sorted by name
            for i, proj in enumerate(sorted(progetti, key=lambda x: x['name'])):
                frame_proj = ctk.CTkFrame(self.frame_scroll_progetti, fg_color="transparent", cursor="hand2")
                frame_proj.pack(fill="x", padx=5, pady=(2,0))
                
                lbl_nome = ctk.CTkLabel(frame_proj, text=proj.get('name', 'Senza Nome'), font=self.font_bold, anchor="w")
                lbl_nome.pack(fill="x")
                lbl_stato = ctk.CTkLabel(frame_proj, text=f"Stato: {proj.get('status')}", anchor="w")
                lbl_stato.pack(fill="x")
                
                # Bind click event to all elements in the frame
                frame_proj.bind("<Button-1>", lambda e, p=proj: self.mostra_dettagli_progetto(p))
                lbl_nome.bind("<Button-1>", lambda e, p=proj: self.mostra_dettagli_progetto(p))
                lbl_stato.bind("<Button-1>", lambda e, p=proj: self.mostra_dettagli_progetto(p))
                
                # Add separator
                if i < len(progetti) - 1:
                    ctk.CTkFrame(self.frame_scroll_progetti, height=1, fg_color="gray").pack(fill="x", padx=5, pady=3)

        except Exception as e:
            tkmb.showerror("Errore", f"Impossibile caricare i progetti:\n{e}")

    # --- Widget Creation for Tabs ---

    def _crea_widgets_dashboard(self, tab):
        """
        Helper method to create all widgets for the 'Dashboard' tab.
        
        Args:
            tab (CTkFrame): The parent 'Dashboard' tab frame.
        """
        tab.grid_columnconfigure(1, weight=1)
        
        # --- Display-only data (Statistics) ---
        ctk.CTkLabel(tab, text="Dati Principali", font=self.font_bold).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        
        self.lbl_dash_cliente = ctk.CTkLabel(tab, text="Cliente: -")
        self.lbl_dash_cliente.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        self.lbl_dash_ore = ctk.CTkLabel(tab, text="Ore Totali: -")
        self.lbl_dash_ore.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        self.lbl_dash_ore_fatt = ctk.CTkLabel(tab, text="Ore Fatturabili: -")
        self.lbl_dash_ore_fatt.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        self.lbl_dash_costo = ctk.CTkLabel(tab, text="Costo Stimato: -")
        self.lbl_dash_costo.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        # --- Editable data ---
        ctk.CTkLabel(tab, text="Modifica Progetto", font=self.font_bold).grid(row=5, column=0, columnspan=2, padx=10, pady=(20, 10), sticky="w")
        
        ctk.CTkLabel(tab, text="Nome Progetto").grid(row=6, column=0, padx=10, pady=5, sticky="w")
        self.entry_dash_nome = ctk.CTkEntry(tab, width=300)
        self.entry_dash_nome.grid(row=6, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(tab, text="Stato").grid(row=7, column=0, padx=10, pady=5, sticky="w")
        self.combo_dash_stato = ctk.CTkComboBox(tab, values=db_progetti.STATI_PROGETTO)
        self.combo_dash_stato.grid(row=7, column=1, padx=10, pady=5, sticky="w")
        
        ctk.CTkLabel(tab, text="Tariffa Oraria (€)").grid(row=8, column=0, padx=10, pady=5, sticky="w")
        self.entry_dash_tariffa = ctk.CTkEntry(tab)
        self.entry_dash_tariffa.grid(row=8, column=1, padx=10, pady=5, sticky="w")
        
        btn_salva = ctk.CTkButton(tab, text="Salva Modifiche Dati", command=self.salva_dati_dashboard)
        btn_salva.grid(row=9, column=1, padx=10, pady=20, sticky="w")
        
        # --- Delete button (Danger Zone) ---
        btn_elimina = ctk.CTkButton(tab, text="ELIMINA PROGETTO", fg_color="#D32F2F", hover_color="#B71C1C",
                                    command=self.elimina_progetto)
        btn_elimina.grid(row=10, column=1, padx=10, pady=20, sticky="w")


    def _crea_widgets_fasi(self, tab):
        """
        Helper method to create all widgets for the 'Fasi' (Phases) tab.
        
        Args:
            tab (CTkFrame): The parent 'Fasi' tab frame.
        """
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        
        btn_add = ctk.CTkButton(tab, text="Aggiungi Fase", command=self.apri_popup_fase)
        btn_add.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.frame_scroll_fasi = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.frame_scroll_fasi.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

    def _crea_widgets_attivita(self, tab):
        """
        Helper method to create all widgets for the 'Attività' (Time Log) tab.
        
        Args:
            tab (CTkFrame): The parent 'Attività' tab frame.
        """
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        
        btn_add = ctk.CTkButton(tab, text="Aggiungi Attività (Time Log)", command=self.apri_popup_attivita)
        btn_add.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.frame_scroll_attivita = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.frame_scroll_attivita.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

    def _crea_widgets_file(self, tab):
        """
        Helper method to create all widgets for the 'File' tab.
        
        Args:
            tab (CTkFrame): The parent 'File' tab frame.
        """
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        
        btn_add = ctk.CTkButton(tab, text="Aggiungi File (Copia)", command=self.aggiungi_file)
        btn_add.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.frame_scroll_file = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.frame_scroll_file.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

    # --- Detail Logic Functions ---

    def mostra_dettagli_progetto(self, progetto):
        """
        Main controller function to load all data for the selected project
        into the entire detail view (all tabs).
        
        Args:
            progetto (dict): The project dictionary to load.
        """
        self.progetto_selezionato = progetto
        self.lbl_titolo_form.configure(text=progetto.get('name'))
        self.tab_view.configure(state="normal") # Enable the tabs
        self.tab_view.set("Dashboard") # Go to the first tab by default
        
        # --- Populate Tab 1: Dashboard ---
        # Calculate fresh stats
        stats = db_progetti.calculate_project_totals(progetto['id'])
        cliente = db_rubrica.find_contact_by_id(progetto['client_id'])
        
        # Update labels
        self.lbl_dash_cliente.configure(text=f"Cliente: {cliente.get('name', 'N/A')}")
        self.lbl_dash_ore.configure(text=f"Ore Totali: {stats['total_ore']:.2f} h")
        self.lbl_dash_ore_fatt.configure(text=f"Ore Fatturabili: {stats['ore_fatturabili']:.2f} h")
        self.lbl_dash_costo.configure(text=f"Costo Stimato (su ore fatt.): {stats['total_costo']:.2f} €")

        # Update entry fields
        self.entry_dash_nome.delete(0, "end")
        self.entry_dash_nome.insert(0, progetto.get('name', ''))
        self.combo_dash_stato.set(progetto.get('status', 'In corso'))
        self.entry_dash_tariffa.delete(0, "end")
        self.entry_dash_tariffa.insert(0, str(progetto.get('tariffa_oraria', '0.0')))
        
        # --- Populate Other Tabs ---
        self._aggiorna_lista_fasi()
        self._aggiorna_lista_attivita()
        self._aggiorna_lista_file()

    def salva_dati_dashboard(self):
        """Saves the main editable data from the Dashboard tab."""
        if not self.progetto_selezionato:
            return
            
        try:
            # Validate data
            tariffa = float(self.entry_dash_tariffa.get())
            dati = {
                'name': self.entry_dash_nome.get(),
                'status': self.combo_dash_stato.get(),
                'tariffa_oraria': tariffa
            }
            # Call backend to update
            db_progetti.update_project(self.progetto_selezionato['id'], dati)
            tkmb.showinfo("Successo", "Dati progetto aggiornati.")
            
            # Refresh lists and detail view to show changes
            self.aggiorna_lista_progetti()
            # Reload the project from DB to get fresh data
            self.mostra_dettagli_progetto(db_progetti.find_project_by_id(self.progetto_selezionato['id']))
        except ValueError:
            tkmb.showerror("Errore", "La tariffa oraria deve essere un numero.")
        except Exception as e:
            tkmb.showerror("Errore", f"Impossibile salvare i dati: {e}")
            
    def elimina_progetto(self):
        """Deletes the currently selected project after confirmation."""
        if not self.progetto_selezionato:
            return

        nome = self.progetto_selezionato['name']
        if not tkmb.askyesno("Conferma Eliminazione", 
                             f"Sei sicuro di voler eliminare '{nome}'?\nTutte le fasi, attività e file verranno persi."):
            return
            
        try:
            db_progetti.delete_project(self.progetto_selezionato['id'])
            tkmb.showinfo("Successo", f"Progetto '{nome}' eliminato.")
            self.on_show() # Refresh the whole page (clears detail, reloads list)
        except Exception as e:
            tkmb.showerror("Errore", f"Impossibile eliminare il progetto:\n{e}")

    # --- Fasi (Phases) Logic ---
    
    def _aggiorna_lista_fasi(self):
        """Clears and repopulates the list of phases in the 'Fasi' tab."""
        for widget in self.frame_scroll_fasi.winfo_children():
            widget.destroy()
        
        fasi = self.progetto_selezionato.get('fasi', [])
        if not fasi:
            ctk.CTkLabel(self.frame_scroll_fasi, text="Nessuna fase definita.").pack()
            return

        # Display phases sorted by due date
        for f in sorted(fasi, key=lambda x: x.get('scadenza', '9999')):
            stato_fase = "✅ Completata" if f['completata'] else "⏳ In Corso"
            testo = f"[{stato_fase}] {f['nome']} (Scadenza: {f.get('scadenza', 'N/D')})"
            
            frame_fase = ctk.CTkFrame(self.frame_scroll_fasi, fg_color="transparent")
            frame_fase.pack(fill="x", padx=5, pady=2)
            
            ctk.CTkLabel(frame_fase, text=testo, anchor="w").pack(side="left", fill="x", expand=True)
            
            btn_toggle = ctk.CTkButton(frame_fase, text="Toggle Stato", width=80,
                                       command=lambda id=f['id']: self.toggle_fase(id))
            btn_toggle.pack(side="left", padx=5)
            
            btn_del = ctk.CTkButton(frame_fase, text="X", width=30, fg_color="#D32F2F", hover_color="#B71C1C",
                                    command=lambda id=f['id']: self.elimina_fase(id))
            btn_del.pack(side="left", padx=5)

    def apri_popup_fase(self):
        """Opens a modal Toplevel window to add a new phase."""
        if not self.progetto_selezionato: return

        popup = ctk.CTkToplevel(self)
        popup.title("Aggiungi Fase")
        popup.geometry("400x200")
        
        ctk.CTkLabel(popup, text="Nome Fase:").pack(pady=(10,0))
        entry_nome = ctk.CTkEntry(popup, width=300)
        entry_nome.pack(pady=5, padx=10, fill="x")
        
        ctk.CTkLabel(popup, text="Scadenza (YYYY-MM-DD, opz.):").pack(pady=(10,0))
        entry_scadenza = ctk.CTkEntry(popup, width=300)
        entry_scadenza.pack(pady=5, padx=10, fill="x")
        
        def salva_fase():
            """Nested callback to save the new phase."""
            nome = entry_nome.get()
            scadenza = entry_scadenza.get() or None
            if not nome:
                tkmb.showwarning("Dati Mancanti", "Il nome è obbligatorio.", parent=popup)
                return
            
            # Call backend to add the phase
            db_progetti.add_fase_to_project(self.progetto_selezionato['id'], nome, scadenza)
            # Refresh data
            self.mostra_dettagli_progetto(db_progetti.find_project_by_id(self.progetto_selezionato['id']))
            popup.destroy()

        ctk.CTkButton(popup, text="Salva Fase", command=salva_fase).pack(pady=10)
        popup.transient(self) # Keep popup on top
        popup.grab_set() # Modal
        self.wait_window(popup) # Wait until popup is closed
        
    def toggle_fase(self, fase_id):
        """Toggles the 'completata' status of a phase."""
        if not tkmb.askyesno("Conferma", "Vuoi cambiare lo stato di questa fase?"):
            return
        db_progetti.toggle_fase_status(self.progetto_selezionato['id'], fase_id)
        # Reload the project to show changes
        self.mostra_dettagli_progetto(db_progetti.find_project_by_id(self.progetto_selezionato['id']))
        
    def elimina_fase(self, fase_id):
        """Deletes a phase from the project."""
        if not tkmb.askyesno("Conferma", "Vuoi eliminare questa fase?"):
            return
        db_progetti.delete_fase(self.progetto_selezionato['id'], fase_id)
        # Reload the project to show changes
        self.mostra_dettagli_progetto(db_progetti.find_project_by_id(self.progetto_selezionato['id']))

    # --- Attività (Time Log) Logic ---
    
    def _aggiorna_lista_attivita(self):
        """Clears and repopulates the list of activities (time logs) in the 'Attività' tab."""
        for widget in self.frame_scroll_attivita.winfo_children():
            widget.destroy()
            
        attivita = self.progetto_selezionato.get('attivita', [])
        if not attivita:
            ctk.CTkLabel(self.frame_scroll_attivita, text="Nessuna attività registrata.").pack()
            return

        # Display activities sorted by date (newest first)
        for a in sorted(attivita, key=lambda x: x.get('data', '0000'), reverse=True):
            stato_fatt = "[Fatt.]" if a.get('fatturabile', True) else "[Non-Fatt.]"
            testo = f"{a['data']}: {a['ore']}h {stato_fatt} - {a['descrizione']}"
            
            frame_att = ctk.CTkFrame(self.frame_scroll_attivita, fg_color="transparent")
            frame_att.pack(fill="x", padx=5, pady=2)
            
            ctk.CTkLabel(frame_att, text=testo, anchor="w").pack(side="left", fill="x", expand=True)
            
            btn_del = ctk.CTkButton(frame_att, text="X", width=30, fg_color="#D32F2F", hover_color="#B71C1C",
                                    command=lambda id=a['id']: self.elimina_attivita(id))
            btn_del.pack(side="left", padx=5)

    def apri_popup_attivita(self):
        """Opens a modal Toplevel window to add a new time log (activity)."""
        if not self.progetto_selezionato: return

        popup = ctk.CTkToplevel(self)
        popup.title("Aggiungi Attività")
        popup.geometry("400x350")
        
        ctk.CTkLabel(popup, text="Data (YYYY-MM-DD):").pack(pady=(10,0))
        entry_data = ctk.CTkEntry(popup, width=300)
        entry_data.insert(0, datetime.now().date().isoformat()) # Default to today
        entry_data.pack(pady=5, padx=10, fill="x")
        
        ctk.CTkLabel(popup, text="Ore (es. 1.5):").pack(pady=(10,0))
        entry_ore = ctk.CTkEntry(popup, width=300)
        entry_ore.pack(pady=5, padx=10, fill="x")
        
        ctk.CTkLabel(popup, text="Descrizione:").pack(pady=(10,0))
        entry_desc = ctk.CTkEntry(popup, width=300)
        entry_desc.pack(pady=5, padx=10, fill="x")
        
        check_fatturabile = ctk.CTkCheckBox(popup, text="Attività Fatturabile", onvalue=True, offvalue=False)
        check_fatturabile.select() # Default to True (billable)
        check_fatturabile.pack(pady=10, padx=10)
        
        def salva_attivita():
            """Nested callback to validate and save the new time log."""
            data = entry_data.get()
            ore = entry_ore.get()
            desc = entry_desc.get()
            fatturabile = check_fatturabile.get()
            
            if not data or not ore or not desc:
                tkmb.showwarning("Dati Mancanti", "Data, Ore e Descrizione sono obbligatori.", parent=popup)
                return
            
            try:
                # Validate date and hour formats
                datetime.strptime(data, '%Y-%m-%d')
                float(ore)
            except ValueError:
                tkmb.showerror("Errore Formato", "Data (YYYY-MM-DD) o Ore (es. 1.5) non validi.", parent=popup)
                return

            # Call backend to add the activity
            db_progetti.add_attivita_to_project(self.progetto_selezionato['id'], data, ore, desc, fatturabile)
            # Reload the project to show changes
            self.mostra_dettagli_progetto(db_progetti.find_project_by_id(self.progetto_selezionato['id']))
            popup.destroy()

        ctk.CTkButton(popup, text="Salva Attività", command=salva_attivita).pack(pady=10)
        popup.transient(self)
        popup.grab_set()
        self.wait_window(popup)

    def elimina_attivita(self, attivita_id):
        """Deletes a time log (activity) from the project."""
        if not tkmb.askyesno("Conferma", "Vuoi eliminare questa attività?"):
            return
        db_progetti.delete_attivita(self.progetto_selezionato['id'], attivita_id)
        # Reload the project to show changes
        self.mostra_dettagli_progetto(db_progetti.find_project_by_id(self.progetto_selezionato['id']))

    # --- File Management Logic ---
    
    def _aggiorna_lista_file(self):
        """Clears and repopulates the list of files in the 'File' tab."""
        for widget in self.frame_scroll_file.winfo_children():
            widget.destroy()
            
        files = self.progetto_selezionato.get('file_archiviati', [])
        
        # Display the full path to the project's file folder
        ctk.CTkLabel(self.frame_scroll_file, text=f"Percorso: {os.path.abspath(db_progetti.get_project_files_path(self.progetto_selezionato['id']))}",
                     font=ctk.CTkFont(size=10, slant="italic")).pack(anchor="w", padx=5)
                     
        if not files:
            ctk.CTkLabel(self.frame_scroll_file, text="Nessun file archiviato.").pack(pady=10)
            return

        # List all files with a delete button
        for f in files:
            frame_file = ctk.CTkFrame(self.frame_scroll_file, fg_color="transparent")
            frame_file.pack(fill="x", padx=5, pady=2)
            
            ctk.CTkLabel(frame_file, text=f"📄 {f}", anchor="w").pack(side="left", fill="x", expand=True)
            
            btn_del = ctk.CTkButton(frame_file, text="X", width=30, fg_color="#D32F2F", hover_color="#B71C1C",
                                    command=lambda nome=f: self.elimina_file(nome))
            btn_del.pack(side="left", padx=5)

    def aggiungi_file(self):
        """
        Opens a file dialog to select a file, then copies that file
        into the project's dedicated folder.
        """
        if not self.progetto_selezionato: return
        
        source_path = filedialog.askopenfilename(title="Seleziona file da copiare")
        if not source_path:
            return # User cancelled
            
        # Call backend to copy the file
        success, msg = db_progetti.add_file_to_project(self.progetto_selezionato['id'], source_path)
        if success:
            tkmb.showinfo("Successo", msg)
            # Reload the project and file list
            self.mostra_dettagli_progetto(db_progetti.find_project_by_id(self.progetto_selezionato['id']))
            self._aggiorna_lista_file() # Redundant but safe
        else:
            tkmb.showerror("Errore", msg)

    def elimina_file(self, filename):
        """Deletes a file from the project's folder."""
        if not tkmb.askyesno("Conferma", f"Vuoi eliminare il file '{filename}'?"):
            return
        db_progetti.delete_file_from_project(self.progetto_selezionato['id'], filename)
        # Reload the project and file list
        self.mostra_dettagli_progetto(db_progetti.find_project_by_id(self.progetto_selezionato['id']))
        self._aggiorna_lista_file() # Redundant but safe

    # --- Project Creation Logic (Popup) ---
    
    def crea_nuovo_progetto_popup(self):
        """Opens a modal Toplevel window to create a new project."""
        
        popup = ctk.CTkToplevel(self)
        popup.title("Nuovo Progetto")
        popup.geometry("500x350")
        
        # --- Client Selection ---
        ctk.CTkLabel(popup, text="Seleziona Cliente*", font=self.font_bold).pack(pady=(10,0))
        
        try:
            clienti = db_rubrica.get_all_contacts()
            # Filter for 'Cliente' type
            clienti_options = [f"{c['name']} ({c.get('company', 'N/A')})" for c in clienti if c.get('type') == 'Cliente']
            clienti_map = {f"{c['name']} ({c.get('company', 'N/A')})": c['id'] for c in clienti if c.get('type') == 'Cliente'}
            
            if not clienti_options:
                tkmb.showerror("Errore", "Nessun 'Cliente' trovato in rubrica. Creane uno prima.", parent=popup)
                popup.destroy()
                return
                
            combo_clienti = ctk.CTkComboBox(popup, values=clienti_options, width=400)
            combo_clienti.pack(pady=5, padx=10)
        except Exception as e:
            tkmb.showerror("Errore", f"Impossibile caricare i clienti: {e}", parent=popup)
            popup.destroy()
            return

        # --- Other Fields ---
        ctk.CTkLabel(popup, text="Nome Progetto*").pack(pady=(10,0))
        entry_nome = ctk.CTkEntry(popup, width=400)
        entry_nome.pack(pady=5, padx=10)
        
        ctk.CTkLabel(popup, text="Tariffa Oraria (€)").pack(pady=(10,0))
        entry_tariffa = ctk.CTkEntry(popup, width=400)
        entry_tariffa.insert(0, "0.0")
        entry_tariffa.pack(pady=5, padx=10)
        
        def salva_progetto():
            """Nested callback to validate and save the new project."""
            nome = entry_nome.get()
            cliente_scelto_str = combo_clienti.get()
            
            if not nome or not cliente_scelto_str:
                tkmb.showwarning("Dati Mancanti", "Cliente e Nome Progetto sono obbligatori.", parent=popup)
                return
            
            try:
                # Build data dictionary
                dati = {
                    'name': nome,
                    'client_id': clienti_map[cliente_scelto_str],
                    'tariffa_oraria': float(entry_tariffa.get() or "0.0")
                }
                
                # Call backend to create
                db_progetti.create_project(dati)
                tkmb.showinfo("Successo", "Progetto creato.", parent=popup)
                
                self.aggiorna_lista_progetti() # Refresh list on main page
                popup.destroy()
                
            except ValueError as e:
                tkmb.showerror("Errore Dati", f"Input non valido: {e}", parent=popup)
            except Exception as e:
                tkmb.showerror("Errore", f"Impossibile salvare il progetto: {e}", parent=popup)

        ctk.CTkButton(popup, text="Salva Nuovo Progetto", command=salva_progetto).pack(pady=20)
        popup.transient(self)
        popup.grab_set()
        self.wait_window(popup)