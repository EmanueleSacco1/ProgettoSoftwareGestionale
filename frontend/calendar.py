import tkinter
import tkinter.messagebox as tkmb
import customtkinter as ctk
from datetime import datetime, timedelta

# Import backend logic
from backend import calendar as db_calendario
from backend import persistence as db
from backend import email_utils

# Import the base class using a relative import
from .page_base import PageBase

class PaginaCalendario(PageBase):
    """
    Page for managing the Calendar and SMTP settings.
    
    This page shows upcoming events and allows configuration
    and testing of email notifications.
    """
    def __init__(self, master):
        """
        Initialize the Calendar page.
        
        Args:
            master: The parent widget (main_content_frame from App).
        """
        super().__init__(master, fg_color="transparent")

        # --- Layout ---
        # Column 0 = Actions/Config, Column 1 = Event List
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)
        
        # --- Column 0: Actions and Config ---
        frame_azioni = ctk.CTkFrame(self)
        frame_azioni.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        frame_azioni.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame_azioni, text="Calendario e Notifiche", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        # --- Event View ---
        ctk.CTkLabel(frame_azioni, text="Visualizza Periodo:").grid(row=1, column=0, padx=15, pady=(10,0), sticky="w")
        
        ctk.CTkButton(frame_azioni, text="Oggi", command=lambda: self.aggiorna_vista_eventi(0)).grid(row=2, column=0, sticky="ew", padx=15, pady=5)
        ctk.CTkButton(frame_azioni, text="Prossimi 7 giorni", command=lambda: self.aggiorna_vista_eventi(7)).grid(row=3, column=0, sticky="ew", padx=15, pady=5)
        ctk.CTkButton(frame_azioni, text="Prossimi 30 giorni", command=lambda: self.aggiorna_vista_eventi(30)).grid(row=4, column=0, sticky="ew", padx=15, pady=5)

        ctk.CTkFrame(frame_azioni, height=2, fg_color="gray").grid(row=5, column=0, sticky="ew", padx=10, pady=10)
        
        # --- Event Actions ---
        ctk.CTkButton(frame_azioni, text="Aggiungi Evento Manuale", command=self.apri_popup_evento_manuale).grid(row=6, column=0, sticky="ew", padx=15, pady=5)
        ctk.CTkButton(frame_azioni, text="Aggiorna Scadenze Automatiche", command=self.aggiorna_scadenze_auto).grid(row=7, column=0, sticky="ew", padx=15, pady=5)
        
        ctk.CTkFrame(frame_azioni, height=2, fg_color="gray").grid(row=8, column=0, sticky="ew", padx=10, pady=10)

        # --- Email Config ---
        ctk.CTkLabel(frame_azioni, text="Configurazione Email", font=ctk.CTkFont(weight="bold")).grid(row=9, column=0, padx=15, pady=10, sticky="w")
        
        self.btn_config_smtp = ctk.CTkButton(frame_azioni, text="Configura SMTP", command=self.apri_popup_config_smtp)
        self.btn_config_smtp.grid(row=10, column=0, sticky="ew", padx=15, pady=5)
        
        self.btn_test_email = ctk.CTkButton(frame_azioni, text="Invia Email di Test", command=self.invia_test_email)
        self.btn_test_email.grid(row=11, column=0, sticky="ew", padx=15, pady=5)

        # --- Column 1: Event List Display ---
        frame_vista = ctk.CTkFrame(self)
        frame_vista.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
        frame_vista.grid_rowconfigure(1, weight=1)
        frame_vista.grid_columnconfigure(0, weight=1)
        
        self.lbl_titolo_vista = ctk.CTkLabel(frame_vista, text="Scadenze", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_titolo_vista.grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        self.txt_eventi = ctk.CTkTextbox(frame_vista, font=ctk.CTkFont(size=13))
        self.txt_eventi.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        self.txt_eventi.configure(state="disabled")

        self.on_show()

    def on_show(self):
        """
        Overrides PageBase.on_show().
        Called by the main App when this page is raised.
        Refreshes the event list (default 7 days).
        """
        print("Refreshing Calendario page...")
        self.aggiorna_vista_eventi(7) # Default to 7 days view

    def aggiorna_vista_eventi(self, giorni):
        """
        Fetches events for the specified period and displays them
        in the main textbox.
        
        Args:
            giorni (int): 0 for today, 7 for 7 days, 30 for 30 days.
        """
        if giorni == 0:
            self.lbl_titolo_vista.configure(text="Eventi di Oggi")
            start_date = datetime.now().date()
            end_date = start_date
        else:
            self.lbl_titolo_vista.configure(text=f"Eventi prossimi {giorni} giorni")
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=giorni)
            
        try:
            eventi = db_calendario.get_eventi(start_date, end_date)
            
            self.txt_eventi.configure(state="normal")
            self.txt_eventi.delete("1.0", "end")
            
            if not eventi:
                self.txt_eventi.insert("1.0", "Nessun evento trovato per questo periodo.")
            else:
                testo = ""
                current_date_str = ""
                for event in eventi:
                    # Group events by date
                    if event['date'] != current_date_str:
                        current_date_str = event['date']
                        testo += f"\n--- {current_date_str} ---\n"
                    testo += f"  • {event['title']}\n"
                    if event['description']:
                        testo += f"    ({event['description']})\n"
                self.txt_eventi.insert("1.0", testo.strip())
                
            self.txt_eventi.configure(state="disabled")
        except Exception as e:
            tkmb.showerror("Errore", f"Impossibile caricare il calendario: {e}")

    def aggiorna_scadenze_auto(self):
        """Runs the backend function to regenerate automatic deadlines."""
        try:
            count, msg = db_calendario.generate_scadenze_automatiche()
            tkmb.showinfo("Successo", f"{msg} ({count} eventi generati)")
            self.aggiorna_vista_eventi(7) # Refresh the view
        except Exception as e:
            tkmb.showerror("Errore", f"Impossibile aggiornare scadenze: {e}")

    def apri_popup_evento_manuale(self):
        """Opens a Toplevel window to add a new manual event."""
        popup = ctk.CTkToplevel(self)
        popup.title("Aggiungi Evento Manuale")
        popup.geometry("400x250")
        
        ctk.CTkLabel(popup, text="Data (YYYY-MM-DD):").pack(pady=(10,0))
        entry_data = ctk.CTkEntry(popup, width=300)
        entry_data.insert(0, datetime.now().date().isoformat())
        entry_data.pack(pady=5, padx=10, fill="x")
        
        ctk.CTkLabel(popup, text="Titolo:").pack(pady=(10,0))
        entry_titolo = ctk.CTkEntry(popup, width=300)
        entry_titolo.pack(pady=5, padx=10, fill="x")
        
        ctk.CTkLabel(popup, text="Descrizione:").pack(pady=(10,0))
        entry_desc = ctk.CTkEntry(popup, width=300)
        entry_desc.pack(pady=5, padx=10, fill="x")
        
        def salva_evento():
            """Callback to save the manual event."""
            data = entry_data.get()
            titolo = entry_titolo.get()
            desc = entry_desc.get()
            
            if not data or not titolo:
                tkmb.showwarning("Dati Mancanti", "Data e Titolo sono obbligatori.", parent=popup)
                return
            
            try:
                success, msg = db_calendario.create_evento_manuale(data, titolo, desc)
                if success:
                    tkmb.showinfo("Successo", msg, parent=popup)
                    popup.destroy()
                    self.on_show() # Refresh list
                else:
                    tkmb.showerror("Errore", msg, parent=popup)
            except Exception as e:
                tkmb.showerror("Errore", f"Impossibile salvare:\n{e}", parent=popup)

        ctk.CTkButton(popup, text="Salva Evento", command=salva_evento).pack(pady=20)
        
        popup.transient(self) # Keep popup on top
        popup.grab_set() # Modal
        self.wait_window(popup) # Wait until popup is closed

    def apri_popup_config_smtp(self):
        """Opens a Toplevel window to configure SMTP settings."""
        settings = db.load_settings()
        smtp_config = settings.get('smtp_config', {})
        
        popup = ctk.CTkToplevel(self)
        popup.title("Configurazione Server SMTP")
        popup.geometry("450x350")
        
        frame_grid = ctk.CTkFrame(popup, fg_color="transparent")
        frame_grid.pack(fill="both", expand=True, padx=10, pady=10)
        frame_grid.grid_columnconfigure(1, weight=1)
        
        row = 0
        ctk.CTkLabel(frame_grid, text="Host SMTP:").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        entry_host = ctk.CTkEntry(frame_grid)
        entry_host.insert(0, smtp_config.get('host', ''))
        entry_host.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        
        row += 1
        ctk.CTkLabel(frame_grid, text="Porta SMTP:").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        entry_port = ctk.CTkEntry(frame_grid)
        entry_port.insert(0, str(smtp_config.get('port', '587')))
        entry_port.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        
        row += 1
        ctk.CTkLabel(frame_grid, text="Utente (Email):").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        entry_user = ctk.CTkEntry(frame_grid)
        entry_user.insert(0, smtp_config.get('user', ''))
        entry_user.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        
        row += 1
        ctk.CTkLabel(frame_grid, text="Password:").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        entry_pass = ctk.CTkEntry(frame_grid, show="*")
        entry_pass.insert(0, smtp_config.get('password', ''))
        entry_pass.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        
        row += 1
        ctk.CTkLabel(frame_grid, text="Email Notifiche:").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        entry_notify = ctk.CTkEntry(frame_grid)
        entry_notify.insert(0, smtp_config.get('notify_email', ''))
        entry_notify.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        
        def salva_smtp():
            """Callback to save SMTP settings."""
            try:
                new_config = {
                    'host': entry_host.get(),
                    'port': int(entry_port.get()),
                    'user': entry_user.get(),
                    'password': entry_pass.get(),
                    'notify_email': entry_notify.get() or entry_user.get() # Default to user email
                }
                
                settings = db.load_settings()
                settings['smtp_config'] = new_config
                db.save_settings(settings)
                
                tkmb.showinfo("Successo", "Configurazione SMTP salvata.", parent=popup)
                popup.destroy()
                
            except ValueError:
                tkmb.showerror("Errore", "La porta SMTP deve essere un numero.", parent=popup)
            except Exception as e:
                tkmb.showerror("Errore", f"Impossibile salvare: {e}", parent=popup)

        ctk.CTkButton(frame_grid, text="Salva Configurazione", command=salva_smtp).grid(row=row+1, column=1, padx=10, pady=20, sticky="e")
        
        popup.transient(self)
        popup.grab_set()
        self.wait_window(popup)

    def invia_test_email(self):
        """Sends a test email using the saved SMTP settings."""
        settings = db.load_settings()
        smtp_config = settings.get('smtp_config')
        notify_email = smtp_config.get('notify_email', smtp_config.get('user'))

        if not notify_email or not smtp_config.get('host'):
            tkmb.showwarning("Errore", "Configurazione SMTP incompleta. Salva prima le impostazioni.")
            return

        if not tkmb.askyesno("Conferma", f"Inviare un'email di test a {notify_email}?"):
            return
            
        try:
            subject = "Test dal Gestionale Python"
            body = "Se ricevi questa email, la configurazione SMTP funziona."
            
            success, msg = utils_email.send_email(
                recipient_email=notify_email,
                subject=subject,
                body=body,
                smtp_config=smtp_config
            )
            
            if success:
                tkmb.showinfo("Successo", f"Email di test inviata con successo a {notify_email}.")
            else:
                tkmb.showerror("Invio Fallito", f"Impossibile inviare l'email:\n{msg}")
                
        except Exception as e:
            tkmb.showerror("Errore Critico", f"Errore durante l'invio:\n{e}")