import tkinter
import tkinter.messagebox as tkmb
import customtkinter as ctk
from tkinter import filedialog
import os

# Import backend logic
from backend import dashboard as db_dashboard  # Import the correct backend
from backend import address_book as db_rubrica
from backend import projects as db_progetti

# Import the base class using a relative import
from .page_base import PageBase

class PaginaDashboard(PageBase): # --- CLASSE RINOMINATA ---
    """
    The main Dashboard page.
    
    This page displays a summary of all key metrics (KPIs) and provides
    a button to export a comprehensive annual report.
    The layout is refactored for better aesthetics using card-like frames.
    """
    def __init__(self, master):
        """
        Initialize the Dashboard page.
        
        Args:
            master: The parent widget (main_content_frame from App).
        """
        super().__init__(master, fg_color="transparent")

        # --- Layout Configuration ---
        # Configure grid to create a responsive layout of cards
        self.grid_rowconfigure((0, 1), weight=1) # KPI and Detail rows
        self.grid_rowconfigure(2, weight=0)      # Export button row
        self.grid_columnconfigure((0, 1), weight=1) # Two columns for cards
        
        # --- Widgets ---
        
        # --- KPI Row (Row 0) ---
        # This frame holds the top-level financial KPIs
        frame_kpi_row = ctk.CTkFrame(self, fg_color="transparent")
        frame_kpi_row.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=(10, 5))
        frame_kpi_row.grid_columnconfigure((0, 1), weight=1)
        
        # 1. Earnings Statistics Card
        self.frame_guadagni = ctk.CTkFrame(frame_kpi_row)
        self.frame_guadagni.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.frame_guadagni.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.frame_guadagni, text="Statistiche (Anno Corrente)",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=(15, 10), sticky="w")
        
        self.lbl_incassato = ctk.CTkLabel(self.frame_guadagni, text="Incassato (YTD): € 0.00", font=("Arial", 14), anchor="w")
        self.lbl_incassato.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        
        self.lbl_uscite = ctk.CTkLabel(self.frame_guadagni, text="Uscite (YTD): € 0.00", font=("Arial", 14), anchor="w")
        self.lbl_uscite.grid(row=2, column=0, sticky="ew", padx=20, pady=5)
        
        self.lbl_margine = ctk.CTkLabel(self.frame_guadagni, text="Margine (YTD): € 0.00", font=("Arial", 14, "bold"), anchor="w")
        self.lbl_margine.grid(row=3, column=0, sticky="ew", padx=20, pady=(10, 15))

        # 2. Unpaid Invoices Card
        self.frame_fatture = ctk.CTkFrame(frame_kpi_row)
        self.frame_fatture.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.frame_fatture.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.frame_fatture, text="Fatture da Incassare",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=(15, 10), sticky="w")
        
        self.lbl_fatture_count = ctk.CTkLabel(self.frame_fatture, text="0 fatture in attesa", font=("Arial", 14), anchor="w")
        self.lbl_fatture_count.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        
        self.lbl_fatture_totale = ctk.CTkLabel(self.frame_fatture, text="Totale da incassare: € 0.00", font=("Arial", 14, "bold"), anchor="w")
        self.lbl_fatture_totale.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 15))
        
        # --- Detail Row (Row 1) ---
        # This frame holds secondary, non-financial summaries
        frame_detail_row = ctk.CTkFrame(self, fg_color="transparent")
        frame_detail_row.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(5, 10))
        frame_detail_row.grid_columnconfigure((0, 1), weight=1)
        frame_detail_row.grid_rowconfigure(0, weight=1)

        # 3. Active Projects Card
        self.frame_progetti = ctk.CTkFrame(frame_detail_row)
        self.frame_progetti.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.frame_progetti.grid_columnconfigure(0, weight=1)
        self.frame_progetti.grid_rowconfigure(2, weight=1) # Allow textbox to expand

        ctk.CTkLabel(self.frame_progetti, text="Progetti Attivi",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=(15, 10), sticky="w")
        
        self.lbl_progetti_count = ctk.CTkLabel(self.frame_progetti, text="0 progetti in corso", font=("Arial", 14), anchor="w")
        self.lbl_progetti_count.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        
        # Use a read-only Textbox for a scrollable, formatted list
        self.txt_progetti_lista = ctk.CTkTextbox(self.frame_progetti, font=("Arial", 12), activate_scrollbars=False)
        self.txt_progetti_lista.grid(row=2, column=0, sticky="nsew", padx=15, pady=(5, 15))
        self.txt_progetti_lista.configure(state="disabled") # Make read-only

        # 4. Upcoming Deadlines Card
        self.frame_scadenze = ctk.CTkFrame(frame_detail_row)
        self.frame_scadenze.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.frame_scadenze.grid_columnconfigure(0, weight=1)
        self.frame_scadenze.grid_rowconfigure(1, weight=1) # Allow textbox to expand

        ctk.CTkLabel(self.frame_scadenze, text="Scadenze Imminenti (7gg)",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=(15, 10), sticky="w")
        
        # Use a read-only Textbox for the list
        self.txt_scadenze_lista = ctk.CTkTextbox(self.frame_scadenze, font=("Arial", 12))
        self.txt_scadenze_lista.grid(row=1, column=0, sticky="nsew", padx=15, pady=(5, 15))
        self.txt_scadenze_lista.configure(state="disabled") # Make read-only
        
        # --- Report Export Button (Row 2) ---
        self.btn_export = ctk.CTkButton(self, text="Esporta Report Annuale Completo (PDF/Excel)",
                                        command=self.esporta_report_completo)
        self.btn_export.grid(row=2, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 15))
        
        # Load data on first show
        self.on_show()

    def on_show(self):
        """
        Overrides the PageBase method.
        Called when the page is raised by the main app. 
        Refreshes all data on the dashboard by calling the backend.
        """
        print("Refreshing Dashboard page...")
        try:
            # Fetch all dashboard data from the backend in one call
            # --- CHIAMATA CORRETTA ---
            dati = db_dashboard.get_dashboard_data()
            # --- FINE CORREZIONE ---
            
            # 1. Update Earnings Card
            self.lbl_incassato.configure(text=f"Incassato (YTD):   {dati['incassato_ytd']:.2f} €")
            self.lbl_uscite.configure(text=f"Uscite (YTD):      {dati['uscite_ytd']:.2f} €")
            self.lbl_margine.configure(text=f"Margine (YTD):     {dati['margine_ytd']:.2f} €")

            # 2. Update Invoices Card
            self.lbl_fatture_count.configure(text=f"{dati['fatture_da_incassare_count']} fatture in attesa")
            self.lbl_fatture_totale.configure(text=f"Totale da incassare: {dati['fatture_da_incassare_totale']:.2f} €")
            
            # 3. Update Active Projects Card
            self.lbl_progetti_count.configure(text=f"{dati['progetti_attivi_count']} progetti in corso")
            
            # Build the project list string
            progetti_testo = ""
            for p in dati['progetti_attivi_list']:
                progetti_testo += f"• {p['name']}\n"
            if dati['progetti_attivi_count'] > 5: # Limit list length
                progetti_testo += "... e altri."
            if not progetti_testo:
                progetti_testo = "Nessun progetto attivo."
            
            # Update the textbox (must be set to normal, written, then disabled)
            self.txt_progetti_lista.configure(state="normal") 
            self.txt_progetti_lista.delete("1.0", "end")
            self.txt_progetti_lista.insert("1.0", progetti_testo)
            self.txt_progetti_lista.configure(state="disabled")
            
            # 4. Update Upcoming Deadlines Card
            scadenze_testo = ""
            for s in dati['scadenze_imminenti_list']:
                scadenze_testo += f"• {s['date']}: {s['title']}\n"
            if not scadenze_testo:
                scadenze_testo = "Nessuna scadenza imminente."

            # Update the textbox
            self.txt_scadenze_lista.configure(state="normal")
            self.txt_scadenze_lista.delete("1.0", "end")
            self.txt_scadenze_lista.insert("1.0", scadenze_testo)
            self.txt_scadenze_lista.configure(state="disabled")
            
        except Exception as e:
            tkmb.showerror("Errore Dashboard", f"Impossibile caricare i dati del dashboard:\n{e}")

    def esporta_report_completo(self):
        """
        Handles the multi-step process for exporting the comprehensive annual report.
        It asks for the year, the save location/format, and then calls the backend.
        """
        # 1. Ask for the year
        year_dialog = ctk.CTkInputDialog(text="Inserisci l'anno per il report:", title="Anno Report")
        year_str = year_dialog.get_input()
        
        if not year_str:
            return # User cancelled
            
        try:
            year = int(year_str)
        except ValueError:
            tkmb.showerror("Errore", "Anno non valido. Inserire un numero.")
            return
            
        # 2. Ask for the file path and type (Excel or PDF)
        file_path = filedialog.asksaveasfilename(
            title="Salva Report Annuale",
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx"), ("PDF Document", "*.pdf")],
            initialfile=f"report_annuale_{year}"
        )
        
        if not file_path:
            return # User cancelled
            
        # Determine format from the chosen file extension
        file_format = 'pdf' if file_path.endswith('.pdf') else 'excel'
        
        # 3. Call the backend to generate and save the report
        try:
            print(f"Generazione report {file_format} per l'anno {year} in corso...")
            success, msg = db_dashboard.export_report_completo(year, file_format)
            
            if success:
                tkmb.showinfo("Successo", f"Report generato con successo!\n{msg}")
                # Try to open the folder containing the new file
                try:
                    os.startfile(os.path.dirname(file_path))
                except Exception:
                    # Fail silently if os.startfile is not supported
                    print(f"Could not auto-open directory: {os.path.dirname(file_path)}")
            else:
                tkmb.showerror("Errore", f"Impossibile generare il report:\n{msg}")
                
        except Exception as e:
            tkmb.showerror("Errore Critico", f"Errore imprevisto durante l'esportazione:\n{e}")