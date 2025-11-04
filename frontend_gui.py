import tkinter
import tkinter.messagebox
import customtkinter as ctk
import os

# --- Import Updated Backend Modules ---
# Import business logic from the 'backend' package
from backend import persistence as db
from backend import projects as db_progetti
from backend import documents as db_docs
from backend import calendar as db_calendario
# --- End Updated Imports ---

# --- Import GUI Pages ---
# Import page classes from the 'frontend' package
from frontend.page_base import PageBase
from frontend.dashboard import PaginaCruscotto
from frontend.address_book import PaginaRubrica
from frontend.projects import PaginaProgetti
from frontend.documents import PaginaDocumenti
from frontend.ledger import PaginaContabilita
from frontend.calendar import PaginaCalendario
from frontend.time_reports import PaginaReportOre
from frontend.inventory import PaginaMagazzino
# --- End GUI Page Imports ---


# --- Application-wide Settings ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    """
    Main Application Class (GUI Shell).
    
    This class builds the main window, the navigation sidebar,
    and manages switching between the different pages (frames).
    It does not contain the logic for the pages themselves.
    """
    def __init__(self):
        super().__init__()

        self.title("Gestionale Freelancer v2.0")
        self.geometry("1100x720")
        
        # --- Main Layout (Sidebar | Content) ---
        # Column 0 = Sidebar, Column 1 = Main Content
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Navigation Sidebar (Column 0) ---
        self.navigation_frame = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(9, weight=1) # Pushes "Esci" to the bottom

        self.navigation_frame_label = ctk.CTkLabel(self.navigation_frame, 
                                                   text="Gestionale",
                                                   font=ctk.CTkFont(size=20, weight="bold"))
        self.navigation_frame_label.grid(row=0, column=0, padx=20, pady=20)

        # --- Navigation Buttons ---
        self.buttons = {}
        # The 'name' (e.g., "cruscotto") must match the keys in the 'self.frames' dict
        menu_items = [
            ("cruscotto", "Cruscotto"),
            ("rubrica", "Rubrica"),
            ("progetti", "Progetti"),
            ("documenti", "Documenti"),
            ("contabilita", "Contabilità"),
            ("calendario", "Calendario"),
            ("report_ore", "Report Ore"),
            ("magazzino", "Magazzino")
        ]
        
        # Create a button for each item
        for i, (name, text) in enumerate(menu_items):
            btn = ctk.CTkButton(self.navigation_frame,
                                text=text,
                                # Use lambda to pass the page name to the command
                                command=lambda n=name: self.select_frame_by_name(n),
                                corner_radius=0, 
                                fg_color="transparent",
                                text_align="left", 
                                anchor="w")
            btn.grid(row=i+1, column=0, sticky="ew", padx=10, pady=2)
            self.buttons[name] = btn # Store button to manage its active state

        # --- Exit Button ---
        btn_esci = ctk.CTkButton(self.navigation_frame, text="Esci",
                                  command=self.quit,
                                  fg_color="#D32F2F", hover_color="#B71C1C")
        btn_esci.grid(row=9, column=0, padx=20, pady=20, sticky="s")


        # --- Main Content Area (Column 1) ---
        self.main_content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_content_frame.grid(row=0, column=1, sticky="nsew")
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)

        # --- Page/Frame Dictionary ---
        # We create all pages at startup and store them here.
        self.frames = {}
        # Associate keys (used in buttons) with their corresponding Page Class
        for name, PageClass in {
            "cruscotto": PaginaCruscotto,
            "rubrica": PaginaRubrica,
            "progetti": PaginaProgetti,
            "documenti": PaginaDocumenti,
            "contabilita": PaginaContabilita,
            "calendario": PaginaCalendario,
            "report_ore": PaginaReportOre,
            "magazzino": PaginaMagazzino
        }.items():
            # Create an instance of the page
            frame = PageClass(self.main_content_frame) 
            self.frames[name] = frame
            # Place the frame in the grid. It will be hidden until raised.
            frame.grid(row=0, column=0, sticky="nsew")

        # Show the initial page
        self.select_frame_by_name("cruscotto")

    def select_frame_by_name(self, name):
        """
        Shows the requested page (frame) and hides all others.
        Also updates the navigation button styles.
        
        Args:
            name (str): The key (e.g., "rubrica") of the frame to show.
        """
        
        # Reset all navigation buttons to their default (transparent) color
        for btn_name, btn in self.buttons.items():
            btn.configure(fg_color="transparent")
        
        # Highlight the active button
        active_color = ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        self.buttons[name].configure(fg_color=active_color)
        
        # Get the frame associated with the name
        frame = self.frames[name]
        
        # Lift the selected frame to the top of the stacking order
        frame.tkraise()
        
        # If the page has an 'on_show' method, call it.
        # This allows pages to refresh their data when they become visible.
        if hasattr(frame, "on_show"):
            frame.on_show()

if __name__ == "__main__":
    # --- Application Startup ---
    
    # 1. Ensure required directories exist
    # These paths are imported from the backend modules
    os.makedirs(db_progetti.PROJECT_FILES_DIR, exist_ok=True)
    os.makedirs(db_docs.PDF_EXPORT_DIR, exist_ok=True)
    
    # 2. Run automatic deadline generation on startup
    print("Aggiornamento scadenze automatiche all'avvio...")
    try:
        db_calendario.generate_scadenze_automatiche()
    except Exception as e:
        # This might fail on first run if .pkl files don't exist yet
        print(f"Errore aggiornamento scadenze (file .pkl potrebbero mancare): {e}")

    # 3. Create and run the main application
    app = App()
    app.mainloop()