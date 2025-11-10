import customtkinter as ctk

class PageBase(ctk.CTkFrame):
    """
    A base class for all pages (frames) in the application.
    
    It inherits from CTkFrame and provides a standard structure
    and placeholder methods. All other page classes in the
    'frontend' package (e.g., PaginaDashboard, PaginaProgetti) 
    should inherit from this class.
    """
    def __init__(self, master, *args, **kwargs):
        """
        Initializes the base page frame.
        
        Args:
            master (tk.Frame or ctk.CTkFrame): The parent widget,
                which is typically the 'main_content_frame' from the App class.
            *args, **kwargs: Additional arguments passed to the CTkFrame constructor.
        """
        super().__init__(master, *args, **kwargs)
        
        # Configure the frame's grid to make its content (in row 0, col 0)
        # expand to fill the entire space.
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
    def on_show(self):
        """
        A placeholder method that is called by the main App
        when this page is raised to the front (i.e., becomes visible).
        
        Child pages (like PaginaDashboard, PaginaRubrica, etc.) 
        MUST override this method to refresh their data (e.g., reload
        lists from the database) when they are shown.
        """
        print(f"Showing page: {self.__class__.__name__}")
        # Child classes will override this with:
        # self.refresh_data_list()
        # self.clear_form()
        pass