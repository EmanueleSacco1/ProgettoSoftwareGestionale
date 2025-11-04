import customtkinter as ctk

class PageBase(ctk.CTkFrame):
    """
    A base class for all pages (frames) in the application.
    
    It inherits from CTkFrame and provides a standard structure.
    All other pages will inherit from this class.
    """
    def __init__(self, master, *args, **kwargs):
        """
        Initializes the base page frame.
        
        Args:
            master (tk.Frame or ctk.CTkFrame): The parent widget,
                which is the main_content_frame from the App class.
        """
        super().__init__(master, *args, **kwargs)
        
        # Configure the frame to take up all available space
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
    def on_show(self):
        """
        A placeholder method that can be called by the main App
        when the page is raised to the front.
        
        Child pages will override this method to refresh their
        data when they become visible.
        """
        print(f"Showing page: {self.__class__.__name__}")
        pass