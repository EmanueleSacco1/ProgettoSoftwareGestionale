import tkinter
import tkinter.messagebox as tkmb
import customtkinter as ctk
from datetime import datetime
import os

# Import backend logic
from backend import time_reports as db_reporting

# Import the base class
from .page_base import PageBase

class PaginaReportOre(PageBase):
    """
    Page for displaying Time-Tracking Reports and Productivity Charts.
    
    This page provides filters for date ranges and years, allowing
    the user to generate text-based summaries or image-based charts.
    """
    def __init__(self, master):
        """
        Initialize the Time Reports page.
        
        Args:
            master: The parent widget (main_content_frame from App).
        """
        super().__init__(master)
        
        # Remove the "Under Construction" label from PageBase if it exists
        for widget in self.winfo_children():
            widget.destroy()

        # Configure layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Make the results textbox expandable

        # --- Top Frame: Actions/Filters ---
        frame_azioni = ctk.CTkFrame(self)
        frame_azioni.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        # Date Range filters
        ctk.CTkLabel(frame_azioni, text="Filtra per Periodo (YYYY-MM-DD):").pack(side="left", padx=(10,5))
        
        self.entry_start_date = ctk.CTkEntry(frame_azioni, width=120, placeholder_text="Data Inizio")
        self.entry_start_date.pack(side="left", padx=5)
        
        self.entry_end_date = ctk.CTkEntry(frame_azioni, width=120, placeholder_text="Data Fine")
        self.entry_end_date.pack(side="left", padx=5)

        ctk.CTkButton(frame_azioni, text="Genera Report Periodo", command=self.genera_report_periodo).pack(side="left", padx=10)

        # Separator
        ctk.CTkFrame(frame_azioni, width=2, fg_color="gray").pack(side="left", fill="y", padx=10, pady=5)
        
        # Annual Chart filters
        self.entry_year = ctk.CTkEntry(frame_azioni, width=80, placeholder_text=str(datetime.now().year))
        self.entry_year.pack(side="left", padx=5)
        ctk.CTkButton(frame_azioni, text="Genera Grafico Annuale", command=self.genera_grafico_annuale).pack(side="left", padx=10)

        # --- Main Content: Results Textbox ---
        # A read-only textbox to display text reports
        self.txt_risultati = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Monospace", size=13))
        self.txt_risultati.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        self.on_show()

    def on_show(self):
        """
        Overrides PageBase.on_show().
        Called by the main App when this page is raised.
        Clears the results text area and shows a placeholder.
        """
        print("Refreshing Report Ore page...")
        self.txt_risultati.configure(state="normal")
        self.txt_risultati.delete("1.0", "end")
        self.txt_risultati.insert("1.0", "Seleziona un periodo o un anno e genera un report.")
        self.txt_risultati.configure(state="disabled")

    def _get_date_range(self):
        """
        Helper function to get and validate the date range from the entry fields.
        If fields are empty, it defaults to the current month (from 1st to today).
        
        Returns:
            tuple (datetime, datetime): (start_date, end_date) or (None, None) on error.
        """
        try:
            today = datetime.now().date()
            # Default to first day of current month if empty
            start_str = self.entry_start_date.get() or today.replace(day=1).isoformat()
            # Default to today if empty
            end_str = self.entry_end_date.get() or today.isoformat()
            
            # Parse strings to datetime objects
            start_date = datetime.strptime(start_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_str, '%Y-%m-%d')
            
            return start_date, end_date
        except ValueError:
            tkmb.showerror("Errore Data", "Formato data non valido. Usare YYYY-MM-DD.")
            return None, None

    def genera_report_periodo(self):
        """
        Generates the text-based summary report for the selected period
        by calling multiple backend functions and combining their results.
        Displays the final string in the textbox.
        """
        start_date, end_date = self._get_date_range()
        if not start_date:
            return # Error already shown by _get_date_range

        # Call backend functions
        report_ore, msg_ore = db_reporting.generate_report_ore(start_date, end_date)
        report_progetti, report_clienti, msg_proj = db_reporting.generate_analisi_progetti_onerose(start_date, end_date)
        
        # --- Build Output String ---
        output = f"--- REPORT PER PERIODO: {start_date.date().isoformat()} -> {end_date.date().isoformat()} ---\n\n"
        
        # Section 1: Billable Hours Summary
        output += "--- Riepilogo Ore ---\n"
        if not report_ore:
            output += f"{msg_ore}\n"
        else:
            output += f"  Ore FATTURABILI:   {report_ore['fatturabili']:.2f} h\n"
            output += f"  Ore NON FATTURABILI: {report_ore['non_fatturabili']:.2f} h\n"
            output += "  -----------------------\n"
            output += f"  ORE TOTALI:          {report_ore['totali']:.2f} h\n"
            try:
                # Calculate billable percentage
                perc = (report_ore['fatturabili'] / report_ore['totali']) * 100
                output += f"  Percentuale Fatturabile: {perc:.1f} %\n"
            except ZeroDivisionError:
                pass
        
        # Section 2: Hours per Project
        output += "\n--- Ore per Progetto ---\n"
        if report_progetti is None or report_progetti.empty:
            output += f"{msg_proj}\n"
        else:
            # Convert pandas Series to string for display
            output += report_progetti.to_string(float_format="%.2f h") + "\n"
            
        # Section 3: Hours per Client
        output += "\n--- Ore per Cliente ---\n"
        if report_clienti is None or report_clienti.empty:
            output += f"{msg_proj}\n"
        else:
            # Convert pandas Series to string for display
            output += report_clienti.to_string(float_format="%.2f h") + "\n"

        # --- Display Results ---
        self.txt_risultati.configure(state="normal") # Enable writing
        self.txt_risultati.delete("1.0", "end")
        self.txt_risultati.insert("1.0", output)
        self.txt_risultati.configure(state="disabled") # Make read-only

    def genera_grafico_annuale(self):
        """
        Generates and saves the annual productivity chart (.png)
        for the selected year. Attempts to open the saved file.
        """
        try:
            # Default to current year if entry is empty
            year_str = self.entry_year.get() or str(datetime.now().year)
            year = int(year_str)
            filename = f"produttivita_{year}.png"
            
            print(f"Generazione grafico per l'anno {year}...")
            # Call backend function to create and save the plot
            success, msg = db_reporting.plot_produttivita_mensile(year, filename)
            
            if success:
                tkmb.showinfo("Grafico Generato", f"Grafico salvato con successo in:\n{os.path.abspath(filename)}")
                # Attempt to open the saved file with the default system viewer
                try:
                    os.startfile(os.path.abspath(filename))
                except Exception:
                    print(f"Could not auto-open file: {filename}")
            else:
                tkmb.showwarning("Errore Grafico", msg)
                
        except ValueError:
            tkmb.showerror("Errore Anno", "Anno non valido. Inserire un numero (es. 2025).")
        except Exception as e:
            tkmb.showerror("Errore", f"Impossibile generare il grafico: {e}")