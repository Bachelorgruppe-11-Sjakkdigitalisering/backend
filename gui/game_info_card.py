import customtkinter as ctk

class GameInfoCard(ctk.CTkFrame):
  """
  A reusable card component displaying game details and tracking controls.
  """
  def __init__(self, master, white_player, black_player, status_text):
    super().__init__(master, border_width=1)
    self._build_ui(white_player, black_player, status_text)

  def _build_ui(self, white_player, black_player, status_text):
    """Constructs the grid layout of the card."""
    self.grid_columnconfigure(0, weight=1)

    # Headline
    headline_text = f"{white_player} (W) vs {black_player} (B)"
    self.headline_label = ctk.CTkLabel(self, text=headline_text)
    self.headline_label.grid(row=0, column=0, sticky="w")

    # Status text
    self.status_label = ctk.CTkLabel(self, text=status_text)
    self.status_label.grid(row=1, column=0, sticky="w")

    # Button group
    self.button_frame = ctk.CTkFrame(self)
    self.button_frame.grid(row=2, column=0)

    # Vis live feed button
    self.btn_live_feed = ctk.CTkButton(self.button_frame, text="Vis live feed")
    self.btn_live_feed.pack(side="left")

    # Stopp tracking button
    self.btn_stop_tracking = ctk.CTkButton(self.button_frame, text="Stopp tracking")
    self.btn_stop_tracking.pack(side="left")

  def update_status(self, new_status_text: str):
    """Update the status text."""
    self.status_label.configure(text=new_status_text)

  def connect_live_feed_callback(self, callback):
    """Connect live feed view button to open actual live feed."""
    self.btn_live_feed.configure(command=callback)

  def connect_stop_tracking_callback(self, callback):
    """Connect stop tracking button to a function in the dashboard."""
    self.btn_stop_tracking.configure(command=callback)