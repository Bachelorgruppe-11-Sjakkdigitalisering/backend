import customtkinter as ctk
import cv2
import queue
from PIL import Image
from gui.components.game_info_card import GameInfoCard
from gui.components.live_feed_window import LiveFeedWindow
from gui.components.roi_selector_window import ROISelectorWindow
from gui.pages.main_page import MainPage
from gui.pages.pairings_page import PairingsPage
from machine_learning.vision_thread import VisionThread
from network.api_client import ChessAPIClient

class MainAdminDashboard(ctk.CTk):
  def __init__(self):
    super().__init__()
    self.geometry("1100x800")
    self.title("Sjakkdigitalisering Admin Panel")

    self.api_client = ChessAPIClient()
    self.live_window = None
    self.live_camera_id = None

    # State management
    self.tournament_pairings = [] # List of planned/all games
    
    # Dictionary to hold active vision threads and queues
    # Format: { game_id: {"queue": Queue, "worker": VisionThread, "pairing_data": dict} }
    self.active_sessions = {} 

    self._build_ui()
    self._poll_vision_queues() 

  def _build_ui(self):
    # Configure layout of 2 rows and 2 columns
    self.grid_rowconfigure(0, weight=1) # A non-zero weight makes this section expand to fill extra space
    self.grid_rowconfigure(1, weight=0)
    self.grid_columnconfigure(0, weight=0)
    self.grid_columnconfigure(1, weight=1)

    # Left navigation drawer
    self.nav_frame = ctk.CTkFrame(self)
    self.nav_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
    self.btn_nav1 = ctk.CTkButton(self.nav_frame, text="Aktive kamper", command=lambda: self.show_page("MainPage"))
    self.btn_nav1.pack(pady=10, padx=20)
    self.btn_nav2 = ctk.CTkButton(self.nav_frame, text="Oppsett av kamper", command=lambda: self.show_page("PairingsPage"))
    self.btn_nav2.pack(pady=10, padx=20)

    # System logs
    self.log_frame = ctk.CTkFrame(self)
    self.log_frame.grid(row=1, column=1, sticky="nsew")
    self.log_frame.grid_propagate(False)
    self.log_sample = ctk.CTkLabel(self.log_frame, text="12:00:03 - Her er et eksempel på en logg.")
    self.log_sample.pack()

    # Main view
    self.main_container = ctk.CTkFrame(self, fg_color="transparent")
    self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
    self.main_container.grid_rowconfigure(0, weight=1)
    self.main_container.grid_columnconfigure(0, weight=1)

    # Initialize all pages and stack them in the container
    self.pages = {}
    for PageClass in [MainPage, PairingsPage]:
      page_name = PageClass.__name__
      frame = PageClass(parent=self.main_container, controller=self)
      self.pages[page_name] = frame
      frame.grid(row=0, column=0, sticky="nsew")

    self.show_page("MainPage")

  def show_page(self, page_name):
    """Brings the requested page to the front of the stacking order."""
    frame = self.pages[page_name]
    frame.tkraise()

  def get_page(self, page_name: str):
    """Fetches a view instance."""
    return self.pages.get(page_name)

  def toggle_piece_boxes(self, game_id: int):
    """Toggles the visibility of the YOLO piece bounding boxes."""
    worker = self.active_sessions[game_id]["worker"]
    worker.show_piece_boxes = not worker.show_piece_boxes

  def open_roi_selector(self, game_id: int):
    """Grabs one frame from the queue and opens the drawing tool."""
    session = self.active_sessions.get(game_id)
    if not session: return

    try:
      # Grab a frame from this specific game's queue
      data = session["queue"].get_nowait()
      frame_rgb = cv2.cvtColor(data["raw_frame"], cv2.COLOR_BGR2RGB)
      pil_image = Image.fromarray(frame_rgb)

      # Pass the specific worker's callback
      ROISelectorWindow(self, pil_image, callback=session["worker"].set_clock_roi)
    except queue.Empty:
      print("No frame available yet for this camera.")

  def on_live_feed_clicked(self, game_id: int):
    """Triggered whenever the 'Vis live feed' button is clicked."""
    print(f"Opening live feed window for Game {game_id}.")
    self.live_camera_id = game_id

    if self.live_window is None or not self.live_window.winfo_exists():
      self.live_window = LiveFeedWindow(self, controller=self, game_id=game_id)
      
      main_page = self.get_page("MainPage")
      if main_page:
          main_page.update_game_status(game_id, "Status: Live stream active")
    else:
      self.live_window.focus()

  def _poll_vision_queues(self):
    """
    Constantly runs in the background.
    Handles game logic all the time, and updates the UI only if live feed window is open.
    """
    for game_id, session in self.active_sessions.items():
      q = session["queue"]
      pairing = session["pairing_data"]

      try:
        data = q.get_nowait()
        main_page = self.get_page("MainPage")

        status_msg = data.get("status_message")
        if status_msg and main_page:
          main_page.update_game_status(game_id, status_msg)

        # Update Clock State for this specific game
        clock_info = data.get("clock_info")
        if clock_info and clock_info["status"] == "active":
          session["white_time"] = clock_info.get("white", session["white_time"])
          session["black_time"] = clock_info.get("black", session["black_time"])
        
        # Handles moves and API for this specific game
        move_data = data.get("move_data")
        if move_data:
          move_uci = move_data["move_uci"]
          main_page = self.get_page("MainPage")
          if main_page:
            main_page.update_game_status(game_id, f"Status: Siste trekk {move_uci}")

          payload = {
            "board_id": game_id,
            "white_player_name": pairing["white_name"],
            "white_player_id": pairing["white_id"],
            "black_player_name": pairing["black_name"],
            "black_player_id":pairing["black_id"],
            "fen": move_data["fen"],
            "pgn": move_data["pgn"],
            "white_time": session["white_time"],
            "black_time": session["black_time"],
            "is_active": True
          }
          self.api_client.sync_game_state(payload)

        # Handle live feed UI
        if self.live_window is not None and self.live_window.winfo_exists():
          # TODO: ENDRE AT MAN IKKE SJEKKER GAME_ID == KAMERA ID!!!
          if game_id == self.live_camera_id:
            self._update_live_video(data["frame"], data["clock_frame"])
      
      except queue.Empty:
        continue
    
    # Loop again in approx 30ms
    self.after(30, self._poll_vision_queues)

  def _update_live_video(self, board_frame, clock_frame):
    """Helper to handle image conversion and UI drawing."""
    # Convert Board
    board_rgb = cv2.cvtColor(board_frame, cv2.COLOR_BGR2RGB)
    board_pil = Image.fromarray(board_rgb)
    board_ctk = ctk.CTkImage(light_image=board_pil, dark_image=board_pil, size=(600, 400))

    # Convert Clock
    clock_rgb = cv2.cvtColor(clock_frame, cv2.COLOR_BGR2RGB)
    clock_pil = Image.fromarray(clock_rgb)

    # Resize dynamically
    img_w, img_h = clock_pil.size
    if img_w > 0 and img_h > 0:
      ratio = 600 / img_w
      clock_ctk = ctk.CTkImage(light_image=clock_pil, dark_image=clock_pil, size=(600, int(img_h * ratio)))
    else:
      clock_ctk = ctk.CTkImage(light_image=clock_pil, dark_image=clock_pil, size=(600, 150))

    # Push to popup window
    self.live_window.update_feeds(board_ctk, clock_ctk)

  def on_closing(self):
    self.vision_worker.stop()
    self.destroy()

  def on_stop_tracking_clicked(self, game_id):
    print("Disabling tracking.")
    main_page = self.get_page("MainPage")
    if main_page:
      main_page.set_game_status("Status: Paused.")

  def handle_new_pairing(self, data: dict):
    """
    Receives pairing data from the View, validates it, and stores it.
    """
    if not data.get("white_name") or not data.get("black_name") or not data.get("camera_id"):
      print("Feil: Mangler spillernavn eller kamera ID!")
      return
    
    # Assign a mock Game ID 
    # TODO: dette må kanskje komme fra database i fremtiden??
    game_id = len(self.tournament_pairings) + 1
    
    new_pairing = {
      "game_id": game_id,
      "camera_id": int(data["camera_id"]),
      "white_name": data["white_name"],
      "white_id": data["white_id"],
      "black_name": data["black_name"],
      "black_id": data["black_id"],
      "status": "planned" # Can be 'planned', 'active', or 'finished'
    }

    # Save to controller state
    self.tournament_pairings.append(new_pairing)
    print(f"La til nytt oppsett: {new_pairing}")

    # Tell the view to update its UI
    pairings_page = self.get_page("PairingsPage")
    if pairings_page:
      pairings_page.clear_inputs()
      pairings_page.render_pairings_list(self.tournament_pairings)

  def start_tracking_game(self, game_id: int):
    """Spins up a new vision thread for a specific pairing."""
    pairing = next(
      (pair for pair in self.tournament_pairings if pair["game_id"] == game_id), None
    )
    if not pairing:
      return
    
    # Start camera thread
    q = queue.Queue()
    worker = VisionThread(q, camera_source=int(pairing["camera_id"]))
    worker.start_camera()

    # Store it in state
    self.active_sessions[game_id] = {
      "queue": q,
      "worker": worker,
      "pairing_data": pairing,
      "white_time": "",
      "black_time": ""
    }
    pairing["status"] = "active"

    self.get_page("PairingsPage").render_pairings_list(self.tournament_pairings)
    self.get_page("MainPage").render_active_games(self.active_sessions)

  def lock_board_for_game(self, game_id: int):
    worker = self.active_sessions[game_id]["worker"]
    worker.lock_board()

  def unlock_board_for_game(self, game_id: int):
    worker = self.active_sessions[game_id]["worker"]
    worker.unlock_board()

  def auto_calibrate_game(self, game_id: int):
    worker = self.active_sessions[game_id]["worker"]
    worker.trigger_auto_calibration()

app = MainAdminDashboard()
app.mainloop()