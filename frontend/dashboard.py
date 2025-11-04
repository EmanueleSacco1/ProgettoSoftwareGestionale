import tkinter
import tkinter.messagebox as tkmb
import customtkinter as ctk
from tkinter import filedialog
import os

# Import backend logic
from backend import dashboard as db_cruscotto
from backend import address_book as db_rubrica
from backend import projects as db_progetti

# Import the base class using a relative import
from .page_base import PageBase

class PaginaCruscotto(PageBase):
    """
    The main Dashboard page.
    
    This page displays a summary of all key metrics and provides
    a button to export the comprehensive annual report.
    """
    def __init__(self, master):
        """
        Initialize the Dashboard page.
        
        Args:
            master: The parent widget (main_content_frame from App).
        """
        super().__init__(master, fg_color="transparent")

        # --- Layout ---
        # The page is divided into a 2x2 grid for the summary cards
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # --- Widgets ---
        
        # 1. Earnings Statistics Card (Top-Left)
        self.frame_guadagni = ctk.CTkFrame(self)
        self.frame_guadagni.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self.frame_guadagni.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.frame_guadagni, text="Statistiche (Anno Corrente)",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=(15, 10))
        
        self.lbl_incassato = ctk.CTkLabel(self.frame_guadagni, text="Incassato (YTD): € 0.00", font=("Arial", 14), anchor="w")
        self.lbl_incassato.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        
        self.lbl_uscite = ctk.CTkLabel(self.frame_guadagni, text="Uscite (YTD): € 0.00", font=("Arial", 14), anchor="w")
        self.lbl_uscite.grid(row=2, column=0, sticky="ew", padx=20, pady=5)
        
        self.lbl_margine = ctk.CTkLabel(self.frame_guadagni, text="Margine (YTD): € 0.00", font=("Arial", 14, "bold"), anchor="w")
        self.lbl_margine.grid(row=3, column=0, sticky="ew", padx=20, pady=(5, 15))

        # 2. Unpaid Invoices Card (Top-Right)
        self.frame_fatture = ctk.CTkFrame(self)
        self.frame_fatture.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.frame_fatture.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.frame_fatture, text="Fatture da Incassare",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=(15, 10))
        
        self.lbl_fatture_count = ctk.CTkLabel(self.frame_fatture, text="0 fatture in attesa", font=("Arial", 14), anchor="w")
        self.lbl_fatture_count.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        
        self.lbl_fatture_totale = ctk.CTkLabel(self.frame_fatture, text="Totale da incassare: € 0.00", font=("Arial", 14, "bold"), anchor="w")
        self.lbl_fatture_totale.grid(row=2, column=0, sticky="ew", padx=20, pady=(5, 15))

        # 3. Active Projects Card (Bottom-Left)
        self.frame_progetti = ctk.CTkFrame(self)
        self.frame_progetti.grid(row=1, column=0, sticky="nsew", padx=15, pady=15)
        self.frame_progetti.grid_columnconfigure(0, weight=1)
        self.frame_progetti.grid_rowconfigure(2, weight=1) # Allow list to expand

        ctk.CTkLabel(self.frame_progetti, text="Progetti Attivi",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=(15, 10))
        
        self.lbl_progetti_count = ctk.CTkLabel(self.frame_progetti, text="0 progetti in corso", font=("Arial", 14), anchor="w")
        self.lbl_progetti_count.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        
        # This label will hold the list of project names
        self.lbl_progetti_lista = ctk.CTkLabel(self.frame_progetti, text="", font=("Arial", 12), anchor="nw", justify="left")
        self.lbl_progetti_lista.grid(row=2, column=0, sticky="nsew", padx=20, pady=(5, 15))

        # 4. Upcoming Deadlines Card (Bottom-Right)
        self.frame_scadenze = ctk.CTkFrame(self)
        self.frame_scadenze.grid(row=1, column=1, sticky="nsew", padx=15, pady=15)
        self.frame_scadenze.grid_columnconfigure(0, weight=1)
        self.frame_scadenze.grid_rowconfigure(1, weight=1) # Allow list to expand

        ctk.CTkLabel(self.frame_scadenze, text="Scadenze Imminenti (7gg)",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=(15, 10))
        
        # This label will hold the list of deadlines
        self.lbl_scadenze_lista = ctk.CTkLabel(self.frame_scadenze, text="Nessuna scadenza imminente.", font=("Arial", 12), anchor="nw", justify="left")
        self.lbl_scadenze_lista.grid(row=1, column=0, sticky="nsew", padx=20, pady=(5, 15))
        
        # --- Report Export Button ---
        # Spans both columns at the bottom
        self.btn_export = ctk.CTkButton(self, text="Esporta Report Annuale Completo (PDF/Excel)",
                                        command=self.esporta_report_completo)
        self.btn_export.grid(row=2, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 15))
        
        # Load data on first show
        self.on_show()

    def on_show(self):
        """
        Overrides the PageBase method.
        Called when the page is raised. Refreshes all data on the dashboard.
        """
        print("Refreshing Dashboard page...")
        try:
            dati = db_cruscotto.get_dati_cruscotto()
            
            # 1. Update Earnings
            self.lbl_incassato.configure(text=f"Incassato (YTD):   {dati['incassato_ytd']:.2f} €")
            self.lbl_uscite.configure(text=f"Uscite (YTD):      {dati['uscite_ytd']:.2f} €")
            self.lbl_margine.configure(text=f"Margine (YTD):     {dati['margine_ytd']:.2f} €")

            # 2. Update Invoices
            self.lbl_fatture_count.configure(text=f"{dati['fatture_da_incassare_count']} fatture in attesa")
            self.lbl_fatture_totale.configure(text=f"Totale da incassare: {dati['fatture_da_incassare_totale']:.2f} €")
            
            # 3. Update Projects
            self.lbl_progetti_count.configure(text=f"{dati['progetti_attivi_count']} progetti in corso")
            progetti_testo = ""
            for p in dati['progetti_attivi_list']:
                progetti_testo += f"• {p['name']}\n"
            if dati['progetti_attivi_count'] > 5:
                progetti_testo += "... e altri."
            if not progetti_testo:
                progetti_testo = "Nessun progetto attivo."
            self.lbl_progetti_lista.configure(text=progetti_testo)
            
            # 4. Update Deadlines
            scadenze_testo = ""
            for s in dati['scadenze_imminenti_list']:
                scadenze_testo += f"• {s['date']}: {s['title']}\n"
            if not scadenze_testo:
                scadenze_testo = "Nessuna scadenza imminente."
            self.lbl_scadenze_lista.configure(text=scadenze_testo)
            
        except Exception as e:
            tkmb.showerror("Errore Cruscotto", f"Impossibile caricare i dati del cruscotto:\n{e}")

    def esporta_report_completo(self):
        """
        Handles the logic for exporting the comprehensive annual report.
        """
        # 1. Ask for year
        year_dialog = ctk.CTkInputDialog(text="Inserisci l'anno per il report:", title="Anno Report")
        year_str = year_dialog.get_input()
        
        if not year_str:
            return # User cancelled
            
        try:
            year = int(year_str)
        except ValueError:
            tkmb.showerror("Errore", "Anno non valido. Inserire un numero.")
            return
            
        # 2. Ask for file path and type
        file_path = filedialog.asksaveasfilename(
            title="Salva Report Annuale",
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx"), ("PDF Document", "*.pdf")],
            initialfile=f"report_annuale_{year}"
        )
        
        if not file_path:
            return # User cancelled
            
        # Determine format from extension
        file_format = 'pdf' if file_path.endswith('.pdf') else 'excel'
        
        # 3. Call backend to generate the report
        try:
            print(f"Generazione report {file_format} per l'anno {year} in corso...")
            success, msg = db_cruscotto.export_report_completo(year, file_format)
            
            if success:
                tkmb.showinfo("Successo", f"Report generato con successo!\n{msg}")
                # Open the file location
                try:
                    os.startfile(os.path.dirname(file_path))
                except Exception:
                    print(f"Could not auto-open directory: {os.path.dirname(file_path)}")
            else:
                tkmb.showerror("Errore", f"Impossibile generare il report:\n{msg}")
                
        except Exception as e:
            tkmb.showerror("Errore Critico", f"Errore imprevisto durante l'esportazione:\n{e}")