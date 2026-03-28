import customtkinter as ctk
import cv2
import queue
from PIL import Image
from gui.components.game_info_card import GameInfoCard
from gui.components.live_feed_window import LiveFeedWindow
from gui.components.roi_selector_window import ROISelectorWindow
from gui.pages.main_page import MainPage
from machine_learning.vision_thread import VisionThread
from network.api_client import ChessAPIClient

class MainAdminDashboard(ctk.CTk):
  def __init__(self):
    super().__init__()
    self.geometry("1100x800")
    self.title("Sjakkdigitalisering Admin Panel")

    self.live_window = None
    
    self.frame_queue = queue.Queue()
    self.vision_worker = VisionThread(self.frame_queue, camera_source=0)
    self.vision_worker.start_camera()

    # Initialize API and dummy state data
    self.api_client = ChessAPIClient()
    self.current_board_id = 1
    self.white_player = "Dennis Johansen"
    self.black_player = "Herman Lundby-Holen"
    self.white_time = ""
    self.black_time = ""

    self._build_ui()
    self._poll_vision_queue()

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
    for PageClass in [MainPage]:
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

  def toggle_piece_boxes(self):
    """Toggles the visibility of the YOLO piece bounding boxes."""
    main_page = self.get_page("MainPage")
    if self.vision_worker.show_piece_boxes:
      self.vision_worker.show_piece_boxes = False
      main_page.set_toggle_button_text("Vis brikker")
    else:
      self.vision_worker.show_piece_boxes = True
      main_page.set_toggle_button_text("Skjul brikker")

  def open_roi_selector(self):
    """Grabs one frame from the queue and opens the drawing tool."""
    try:
      # Grab raw and clean frame
      data = self.frame_queue.get_nowait()
      raw_frame = data["raw_frame"]

      frame_rgb = cv2.cvtColor(raw_frame, cv2.COLOR_BGR2RGB)
      pil_image = Image.fromarray(frame_rgb)

      ROISelectorWindow(self, pil_image, callback=self.vision_worker.set_clock_roi)
    except queue.Empty:
      print("No frame available yet")

  def on_live_feed_clicked(self):
    """Triggered whenever the 'Vis live feed' button is clicked."""
    print("Opening live feed window.")
    if self.live_window is None or not self.live_window.winfo_exists():
      self.live_window = LiveFeedWindow(self)
      self.pages["MainPage"].game_card.update_status("Status: Live stream active")
    else:
      self.live_window.focus()

  def _poll_vision_queue(self):
    """
    Constantly runs in the background.
    Handles game logic all the time, and updates the UI only if live feed window is open.
    """
    try:
      data = self.frame_queue.get_nowait()

      # Clock state
      clock_info = data.get("clock_info")
      if clock_info and clock_info["status"] == "active":
        self.white_time = clock_info.get("white", self.white_time)
        self.black_time = clock_info.get("black", self.black_time)
      
      # Handles moves and api
      move_data = data.get("move_data")
      if move_data:
        move_uci = move_data["move_uci"]
        main_page = self.get_page("MainPage")
        if main_page:
          main_page.set_game_status(f"Status: Siste trekk {move_uci}")

        payload = {
          "board_id": self.current_board_id,
          "white_player_name": self.white_player,
          "black_player_name": self.black_player,
          "fen": move_data["fen"],
          "pgn": move_data["pgn"],
          "white_time": self.white_time,
          "black_time": self.black_time,
          "is_active": True
        }
        self.api_client.sync_game_state(payload)

      # Handle live feed UI
      if self.live_window is not None and self.live_window.winfo_exists():
        self._update_live_video(data["frame"], data["clock_frame"])
    
    except queue.Empty:
      pass
    
    # Loop again in approx 30ms
    self.after(30, self._poll_vision_queue)

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

  def on_stop_tracking_clicked(self):
    print("Disabling tracking.")
    main_page = self.get_page("MainPage")
    if main_page:
      main_page.set_game_status("Status: Paused.")

app = MainAdminDashboard()
app.mainloop()