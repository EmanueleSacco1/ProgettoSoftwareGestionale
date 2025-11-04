import customtkinter as ctk
import os
from PIL import Image

# --- Import Backend Modules ---
from backend import persistence as db
from backend import projects as db_progetti
from backend import documents as db_docs
from backend import calendar as db_calendario

# --- Import frontend pages ---
from frontend.page_base import PageBase
from frontend.dashboard import PaginaDashboard
from frontend.address_book import PaginaRubrica
from frontend.projects import PaginaProgetti
from frontend.documents import PaginaDocumenti
from frontend.ledger import PaginaLedger
from frontend.calendar import PaginaCalendario
from frontend.time_reports import PaginaReportOre
from frontend.inventory import PaginaMagazzino

# --- CustomTkinter setup ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gestionale Freelancer")
        self.geometry("1200x750")
        self.minsize(1000, 650)

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#1E1E2F")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="Gestionale",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#FFFFFF"
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(25, 15), sticky="w")

        # --- Buttons Sidebar ---
        self.buttons = {}
        menu_items = [
            ("dashboard", "Dashboard"),
            ("rubrica", "Rubrica"),
            ("progetti", "Progetti"),
            ("documenti", "Documenti"),
            ("contabilita", "Contabilità"),
            ("calendario", "Calendario"),
            ("report_ore", "Report Ore"),
            ("magazzino", "Magazzino")
        ]

        for i, (name, text) in enumerate(menu_items):
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                command=lambda n=name: self.select_frame_by_name(n),
                corner_radius=8,
                fg_color="transparent",
                hover_color="#2A2A40",
                anchor="w",
                height=36,
                text_color="#E0E0E0"
            )
            btn.grid(row=i+1, column=0, sticky="ew", padx=15, pady=3)
            self.buttons[name] = btn

        # --- Exit Button ---
        btn_esci = ctk.CTkButton(
            self.sidebar,
            text="Esci",
            command=self.quit,
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            corner_radius=8
        )
        btn_esci.grid(row=10, column=0, padx=15, pady=25, sticky="sew")

        # --- Main content area ---
        self.main_frame = ctk.CTkFrame(self, fg_color="#2B2B3C", corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Optional top bar (for page titles)
        self.header_label = ctk.CTkLabel(
            self.main_frame,
            text="Dashboard",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#FFFFFF"
        )
        self.header_label.grid(row=0, column=0, sticky="nw", padx=20, pady=15)

        # --- Page frames ---
        self.frames = {}
        for name, PageClass in {
            "dashboard": PaginaDashboard,
            "rubrica": PaginaRubrica,
            "progetti": PaginaProgetti,
            "documenti": PaginaDocumenti,
            "contabilita": PaginaLedger,
            "calendario": PaginaCalendario,
            "report_ore": PaginaReportOre,
            "magazzino": PaginaMagazzino
        }.items():
            frame = PageClass(self.main_frame)
            self.frames[name] = frame
            frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        self.select_frame_by_name("dashboard")

    def select_frame_by_name(self, name):
        for btn_name, btn in self.buttons.items():
            btn.configure(fg_color="transparent")

        self.buttons[name].configure(fg_color="#2A2A40")
        frame = self.frames[name]
        frame.tkraise()

        # Update title in header
        self.header_label.configure(text=self.buttons[name].cget("text"))

        if hasattr(frame, "on_show"):
            frame.on_show()


if __name__ == "__main__":
    os.makedirs(db_progetti.PROJECT_FILES_DIR, exist_ok=True)
    os.makedirs(db_docs.PDF_EXPORT_DIR, exist_ok=True)

    try:
        db_calendario.generate_scadenze_automatiche()
    except Exception as e:
        print(f"Errore aggiornamento scadenze: {e}")

    app = App()
    app.mainloop()
