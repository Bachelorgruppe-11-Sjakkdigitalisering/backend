import customtkinter
import subprocess

class MainAdminDashboard(customtkinter.CTk):
  def __init__(self):
    super().__init__()
    self.geometry("1100x800")
    self.title ("Sjakkdigitalisering Admin Panel")

    self._build_ui()

  def _build_ui(self):
    # Configure layout of 2 rows and 2 columns
    self.grid_rowconfigure(0, weight=1)
    self.grid_rowconfigure(1, weight=0)
    self.grid_columnconfigure(0, weight=0)
    self.grid_columnconfigure(1, weight=1)

    # Left navigation drawer
    self.nav_frame = customtkinter.CTkFrame(self)
    self.nav_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
    self.btn_nav1 = customtkinter.CTkButton(self.nav_frame, text="Active Game")
    self.btn_nav1.pack(pady=10, padx=20)

    # Main view
    self.main_frame = customtkinter.CTkFrame(self)
    self.main_frame.grid(row=0, column=1, sticky="nsew")
    self.main_label = customtkinter.CTkLabel(self.main_frame, text="Her kommer hovedvisningen til å være.")
    self.main_label.pack()

    # System logs
    self.log_frame = customtkinter.CTkFrame(self)
    self.log_frame.grid(row=1, column=1)
    self.log_sample = customtkinter.CTkLabel(self.log_frame, text="Her er et eksempel på en logg.")
    self.log_sample.pack()



app = MainAdminDashboard()
app.mainloop()