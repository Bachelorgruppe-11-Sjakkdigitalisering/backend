import customtkinter as ctk
import cv2
from PIL import Image
from components.game_info_card import GameInfoCard
from components.live_feed_window import LiveFeedWindow

class MainAdminDashboard(ctk.CTk):
  def __init__(self):
    super().__init__()
    self.geometry("1100x800")
    self.title("Sjakkdigitalisering Admin Panel")

    self.live_window = None
    self.cap = cv2.VideoCapture(0) # TODO: endre dette til faktisk kamera/modell feed

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
    self.live_window = LiveFeedWindow(self)
    self.game_card.update_status("Status: Live stream active")

    self._stream_to_live_window()

  def _stream_to_live_window(self):
    """Pulls frames and sends them to the popup window."""
    # Stop loop if window was closed
    if self.live_window is None:
      self.game_card.update_status("Status: Tracking Live (Move 14)")
      return
    
    success, frame = self.cap.read()
    if success:
      frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
      board_pil = Image.fromarray(frame_rgb)
      clock_pil = Image.fromarray(frame_rgb)
      board_ctk = ctk.CTkImage(light_image=board_pil, dark_image=board_pil, size=(600, 400))
      clock_ctk = ctk.CTkImage(light_image=clock_pil, dark_image=clock_pil, size=(600, 150))

      self.live_window.update_feeds(board_ctk, clock_ctk)

    # Loop again in aprox 30ms
    self.after(30, self._stream_to_live_window)

  def on_closing(self):
    if self.cap.isOpened():
      self.cap.release()
    self.destroy()

  def on_stop_tracking_clicked(self):
    print("Disabling tracking.")
    self.game_card.update_status("Status: Paused.")

app = MainAdminDashboard()
app.mainloop()