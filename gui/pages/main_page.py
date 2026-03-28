import customtkinter as ctk

from gui.components.game_info_card import GameInfoCard

class MainPage(ctk.CTkFrame):
  """The page containing all active game trackers."""
  def __init__(self, parent, controller):
    super().__init__(parent, fg_color="transparent")
    self.controller = controller

    self.game_card = GameInfoCard(
      self, 
      white_player=self.controller.white_player, 
      black_player=self.controller.black_player, 
      status_text="Pending"
    )
    self.game_card.grid(row=0, column=0, sticky="new")
    
    self.game_card.connect_live_feed_callback(self.controller.on_live_feed_clicked)
    self.game_card.connect_stop_tracking_callback(self.controller.on_stop_tracking_clicked)

    self.control_frame = ctk.CTkFrame(self)
    self.control_frame.grid(row=1, column=0, sticky="nw", pady=10)

    self.btn_lock_board = ctk.CTkButton(self.control_frame, text="Lås brett perspektiv", command=self.controller.vision_worker.lock_board)
    self.btn_lock_board.pack(side="left", padx=5)

    self.btn_set_clock = ctk.CTkButton(self.control_frame, text="Velg klokkeområde", command=self.controller.open_roi_selector)
    self.btn_set_clock.pack(side="left", padx=5)

    self.btn_toggle_pieces = ctk.CTkButton(self.control_frame, text="Skjul brikker", command=self.controller.toggle_piece_boxes)
    self.btn_toggle_pieces.pack(side="left", padx=5)

  def set_game_status(self, text: str):
    """Updates the card status."""
    self.game_card.update_status(text)

  def set_toggle_button_text(self, text: str):
    """Updates the toggle button text."""
    self.btn_toggle_pieces.configure(text=text)