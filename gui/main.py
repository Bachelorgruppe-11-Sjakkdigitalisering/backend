import customtkinter as ctk
import cv2
import queue
from PIL import Image
from gui.components.game_info_card import GameInfoCard
from gui.components.live_feed_window import LiveFeedWindow
from gui.components.roi_selector_window import ROISelectorWindow
from machine_learning.vision_thread import VisionThread

class MainAdminDashboard(ctk.CTk):
  def __init__(self):
    super().__init__()
    self.geometry("1100x800")
    self.title("Sjakkdigitalisering Admin Panel")

    self.live_window = None
    
    self.frame_queue = queue.Queue()
    self.vision_worker = VisionThread(self.frame_queue, camera_source=0)
    self.vision_worker.start_camera()

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

    self.control_frame = ctk.CTkFrame(self.main_frame)
    self.control_frame.grid(row=1, column=0, sticky="nw")

    self.btn_lock_board = ctk.CTkButton(self.control_frame, text="Lås brett perspektiv", command=self.vision_worker.lock_board)
    self.btn_lock_board.pack(side="left")

    self.btn_set_clock = ctk.CTkButton(self.control_frame, text="Velg klokkeområde", command=self.open_roi_selector)
    self.btn_set_clock.pack(side="left")

    self.btn_toggle_pieces = ctk.CTkButton(self.control_frame, text="Skjul brikker", command=self.toggle_piece_boxes)
    self.btn_toggle_pieces.pack(side="left")

  def toggle_piece_boxes(self):
    """Toggles the visibility of the YOLO piece bounding boxes."""
    if self.vision_worker.show_piece_boxes:
      self.vision_worker.show_piece_boxes = False
      self.btn_toggle_pieces.configure(text="Vis brikker")
    else:
      self.vision_worker.show_piece_boxes = True
      self.btn_toggle_pieces.configure(text="Skjul brikker")

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
      self.game_card.update_status("Status: Live stream active")
      self._stream_to_live_window()
    else:
      self.live_window.focus()

  def _stream_to_live_window(self):
    """Pulls frames and sends them to the popup window."""
    # Stop loop if window was closed
    if self.live_window is None or not self.live_window.winfo_exists():
      self.game_card.update_status("Status: Tracking Live (Move 14)")
      self.live_window = None
      return
    
    try:
      # Grab latest frame from background thread
      data = self.frame_queue.get_nowait()
      board_frame = data["frame"]
      clock_frame = data["clock_frame"]

      board_rgb = cv2.cvtColor(board_frame, cv2.COLOR_BGR2RGB)
      board_pil = Image.fromarray(board_rgb)
      board_ctk = ctk.CTkImage(light_image=board_pil, dark_image=board_pil, size=(600, 400))

      clock_rgb = cv2.cvtColor(clock_frame, cv2.COLOR_BGR2RGB)
      clock_pil = Image.fromarray(clock_rgb)

      # Resize based on the crops aspect ratio
      img_w, img_h = clock_pil.size
      if img_w > 0 and img_h > 0:
        ratio = 600 / img_w
        clock_ctk = ctk.CTkImage(light_image=clock_pil, dark_image=clock_pil, size=(600, int(img_h * ratio)))
      else:
        clock_ctk = ctk.CTkImage(light_image=clock_pil, dark_image=clock_pil, size=(600, 150))

      self.live_window.update_feeds(board_ctk, clock_ctk)
    except queue.Empty:
      # If background thread has not produced new frame, just skip
      pass

    # Loop again in aprox 30ms
    self.after(30, self._stream_to_live_window)

  def on_closing(self):
    self.vision_worker.stop()
    self.destroy()

  def on_stop_tracking_clicked(self):
    print("Disabling tracking.")
    self.game_card.update_status("Status: Paused.")

app = MainAdminDashboard()
app.mainloop()