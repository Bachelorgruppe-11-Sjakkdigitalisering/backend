import customtkinter as ctk
from components.game_info_card import GameInfoCard
from components.live_feed_window import LiveFeedWindow

class MainAdminDashboard(ctk.CTk):
  def __init__(self):
    super().__init__()
    self.geometry("1100x800")
    self.title ("Sjakkdigitalisering Admin Panel")

    self._build_ui()

  def _build_ui(self):
    # Configure layout of 2 rows and 2 columns
    self.grid_rowconfigure(0, weight=1) # A non-zero weight makes this section expand to fill extra space
    self.grid_rowconfigure(1, weight=0)
    self.grid_columnconfigure(0, weight=0)
    self.grid_columnconfigure(1, weight=1)

    # Left navigation drawer
    self.nav_frame = ctk.CTkFrame(self)
    self.nav_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
    self.btn_nav1 = ctk.CTkButton(self.nav_frame, text="Active Game")
    self.btn_nav1.pack(pady=10, padx=20)

    # Main view
    self._build_main_view()

    # System logs
    self.log_frame = ctk.CTkFrame(self)
    self.log_frame.grid(row=1, column=1, sticky="nsew")
    self.log_frame.grid_propagate(False)
    self.log_sample = ctk.CTkLabel(self.log_frame, text="12:00:03 - Her er et eksempel på en logg.")
    self.log_sample.pack()

  def _build_main_view(self):
    self.main_frame = ctk.CTkFrame(self)
    self.main_frame.grid(row=0, column=1, sticky="nsew")
    self.game_card = GameInfoCard(self.main_frame, white_player="Dennis Johansen", black_player="Herman Lundby-Holen", status_text="Pending")
    self.game_card.grid(row=0, column=0, sticky="new")
    self.game_card.connect_live_feed_callback(self.on_live_feed_clicked)
    self.game_card.connect_stop_tracking_callback(self.on_stop_tracking_clicked)

  def on_live_feed_clicked(self):
    """Triggered whenever the 'Vis live feed' button is clicked."""
    print("Opening live feed window.")
    LiveFeedWindow(self)

  def on_stop_tracking_clicked(self):
    print("Disabling tracking.")
    self.game_card.update_status("Status: Paused.")

app = MainAdminDashboard()
app.mainloop()