import customtkinter as ctk

class LiveFeedWindow(ctk.CTkToplevel):
  """
  A popup window that displays the main board feed and a cropped clock feed,
  and controls for tuning the computer vision.
  """
  def __init__(self, master, controller, game_id: int):
    super().__init__(master)
    self.controller = controller
    self.game_id = game_id

    self.title(f"Live feed: Parti {game_id}")
    self.geometry("700x800")

    self._build_ui()

  def _build_ui(self):
    self.grid_rowconfigure(0, weight=3)
    self.grid_rowconfigure(1, weight=1)
    self.grid_rowconfigure(2, weight=0)
    self.grid_columnconfigure(0, weight=1)

    # Main board feed
    self.board_frame = ctk.CTkFrame(self)
    self.board_frame.grid(row=0, column=0, sticky="nsew")
    self.board_frame.pack_propagate(False)
    
    self.board_label = ctk.CTkLabel(self.board_frame, text="Loading board feed...")
    self.board_label.pack(expand=True, fill="both")

    # Clock cutout feed
    self.clock_frame = ctk.CTkFrame(self)
    self.clock_frame.grid(row=1, column=0, sticky="nsew")
    self.clock_frame.pack_propagate(False)

    self.clock_label = ctk.CTkLabel(self.clock_frame, text="Loading clock feed...")
    self.clock_label.pack(expand=True, fill="both")

    # Control panel
    self.control_frame = ctk.CTkFrame(self)
    self.control_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))

    self.control_frame.grid_columnconfigure((0, 1, 2), weight=1)

    self.btn_lock = ctk.CTkButton(
      self.control_frame, 
      text="Lås brett", 
      command=lambda: self.controller.lock_board_for_game(self.game_id)
    )
    self.btn_lock.grid(row=0, column=0, padx=5, sticky="ew")

    self.btn_roi = ctk.CTkButton(
      self.control_frame, 
      text="Velg klokkeområde", 
      command=lambda: self.controller.open_roi_selector(self.game_id)
    )
    self.btn_roi.grid(row=0, column=1, padx=5, sticky="ew")

    self.btn_toggle = ctk.CTkButton(
      self.control_frame, 
      text="Skjul brikker", 
      command=self._on_toggle_clicked
    )
    self.btn_toggle.grid(row=0, column=2, padx=5, sticky="ew")

  def _on_toggle_clicked(self):
    """Toggles the button text and tells the controller to toggle the boxes."""
    self.controller.toggle_piece_boxes(self.game_id)
    
    # Update local button text based on current state
    current_text = self.btn_toggle.cget("text")
    new_text = "Vis brikker" if current_text == "Skjul brikker" else "Skjul brikker"
    self.btn_toggle.configure(text=new_text)

  def update_feeds(self, board_image: ctk.CTkImage, clock_image: ctk.CTkImage):
    """Updates the board and clock frames."""
    if board_image:
      self.board_label.configure(image=board_image, text="")
    if clock_image:
      self.clock_label.configure(image=clock_image, text="")