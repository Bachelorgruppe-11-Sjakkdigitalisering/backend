import customtkinter as ctk

from gui.components.game_info_card import GameInfoCard

class MainPage(ctk.CTkFrame):
  """The page containing all active game trackers."""
  def __init__(self, parent, controller):
    super().__init__(parent, fg_color="transparent")
    self.controller = controller

    self.scroll_container = ctk.CTkScrollableFrame(self)
    self.scroll_container.pack(fill="both", expand=True, padx=10, pady=10)

    # Dictionary to keep track of the UI widgets for each game 
    # Format: { game_id: {"card": GameInfoCard, "btn_toggle": CTkButton} }
    self.game_widgets = {}

  def render_active_games(self, active_sessions: dict):
    """Loops through active sessions and generates a control card for each."""
    for widget in self.scroll_container.winfo_children():
      widget.destroy()
    self.game_widgets.clear()

    # Build new elements
    for game_id, session in active_sessions.items():
      pairing = session["pairing_data"]

      # Container for this specific game
      game_wrapper = ctk.CTkFrame(self.scroll_container, border_width=2)
      game_wrapper.pack(fill="x", padx=10, pady=10)

      # Info card
      card = GameInfoCard(
        game_wrapper, 
        white_player=pairing["white_name"], 
        black_player=pairing["black_name"], 
        status_text="Status: Venter på trekk..."
      )
      card.pack(fill="x", padx=10, pady=10)
      
      # Connect callbacks, passing the game_id back to the controller
      card.connect_live_feed_callback(lambda gid=game_id: self.controller.on_live_feed_clicked(gid))
      card.connect_stop_tracking_callback(lambda gid=game_id: self.controller.on_stop_tracking_clicked(gid))

      # Control buttons
      # TODO: Move these to live feed window
      control_frame = ctk.CTkFrame(game_wrapper, fg_color="transparent")
      control_frame.pack(fill="x", padx=10, pady=(0, 10))

      btn_lock = ctk.CTkButton(control_frame, text="Lås brett", command=lambda gid=game_id: self.controller.lock_board_for_game(gid))
      btn_lock.pack(side="left", padx=5)

      btn_roi = ctk.CTkButton(control_frame, text="Velg klokkeområde", command=lambda gid=game_id: self.controller.open_roi_selector(gid))
      btn_roi.pack(side="left", padx=5)

      btn_toggle = ctk.CTkButton(control_frame, text="Skjul brikker", command=lambda gid=game_id: self.controller.toggle_piece_boxes(gid))
      btn_toggle.pack(side="left", padx=5)

      # Save references so we can update text later without re-rendering everything
      self.game_widgets[game_id] = {
        "card": card,
        "btn_toggle": btn_toggle
      }

  def update_game_status(self, game_id: int, text: str):
    if game_id in self.game_widgets:
      self.game_widgets[game_id]["card"].update_status(text)

  def update_toggle_button_text(self, game_id: int, text: str):
    if game_id in self.game_widgets:
      self.game_widgets[game_id]["btn_toggle"].configure(text=text)