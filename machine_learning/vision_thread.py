import threading
import queue
import cv2
import time
import chess
import numpy as np
import chessboard.chessboard as chessboard
import moves.moves as moves
from machine_learning.motion_detector import MotionDetector
from ultralytics import YOLO
from collections import deque

class VisionThread(threading.Thread):
  """
  Background thread that captures video and runs heavy AI models.
  Keeps the main GUI thread from freezing.
  """
  def __init__(self, frame_queue: queue.Queue, camera_source=0):
    super().__init__(daemon=True)

    # Thread and IO state
    self.frame_queue = frame_queue
    self.camera_source = camera_source
    self.is_running = threading.Event()
    self.cap = None

    # AI models
    self.board_model = YOLO('brett.pt')
    self.clock_model = YOLO('klokke.pt')
    self.piece_model = YOLO('brikker100.pt')

    # Board calibration state
    self.history = deque(maxlen=10)
    self.M = None
    self.M_inv = None
    self.show_boxes = True

    # Gameplay and logic state
    self.current_board = chess.Board()
    self.reference_occupied = []
    self.board_is_setup = False
    self.latest_move = None
    self.show_piece_boxes = True
    self.motion_detector = MotionDetector(movement_threshold=5000, required_still_frames=15)

    # Retry logic state
    self.is_checking_move = False
    self.check_counter = 0
    self.MAX_CHECKS = 30

    # Clock state
    self.clock_roi = None

  def start_camera(self):
    """Starts the camera stream."""
    self.cap = cv2.VideoCapture(self.camera_source)
    self.is_running.set()
    self.start() # Starts the run() method in the background

  def stop(self):
    """Safely shuts down the thread and camera."""
    self.is_running.clear()
    if self.cap:
      self.cap.release()

  def lock_board(self):
    """Locks the perspective on the board based on recent frames."""
    self.M, self.M_inv = chessboard.lock_perspective(self.history)
    if self.M is not None:
      print("Vision: Board perspective locked successfully!")
      self.show_boxes = False
    else:
      print("Vision: Not enough data to lock board yet.")

  def set_clock_roi(self, roi):
    """Updates the ROI for the clock cutout. roi is a tuple like this: (x, y, w, h)"""
    self.clock_roi = roi
    print(f"Vision: Clock ROI set to {roi}")

  def run(self):
    """The main loop running in the background thread."""
    while self.is_running.is_set():
      if not self.cap or not self.cap.isOpened():
        time.sleep(0.1)
        continue
      
      success, frame = self.cap.read()
      if not success:
        continue

      # Process board and pieces
      if self.M_inv is None or self.show_boxes:
        board_display = self._process_board_calibration(frame)
      else:
        board_display = self._process_active_gameplay(frame)

      # Process clock
      clock_display = self._process_clock(frame)

      # Send to GUI
      self._send_to_gui(frame, board_display, clock_display)

  def _process_board_calibration(self, frame):
    """Finds board corners before perspective is locked."""
    display_frame = frame.copy()
    results = self.board_model(frame, conf=0.05, verbose=False, iou=0.1)

    if self.show_boxes:
      display_frame = results[0].plot()

    corners = chessboard.extract_corners(results)
    if corners is not None:
      self.history.append(corners)

    return display_frame
  
  def _process_active_gameplay(self, frame):
    """Handles motion detection, piece logic, and drawing the grid."""
    display_frame = frame.copy()
    chessboard.draw_grid(display_frame, self.M_inv)

    warped_board = cv2.warpPerspective(frame, self.M, (800, 800))
    motion_state = self.motion_detector.update(warped_board)

    if not self.board_is_setup and motion_state == "IDLE":
      self.reference_occupied = moves.get_occupied_squares_on_raw_frame(frame, self.piece_model, self.M)
      self.board_is_setup = True
      print(f"Initial board setup complete! {len(self.reference_occupied)} pieces found.")

    elif motion_state == "MOTION":
      if self.is_checking_move:
        print("Hand returned! Cancelling move check.")
      self.is_checking_move = False

    elif motion_state == "SETTLED" and self.board_is_setup:
      print("Board settled! Checking for move...")
      self.is_checking_move = True
      self.check_counter = 0

    if self.is_checking_move:
      self.check_counter += 1

      current_occupied = moves.get_occupied_squares_on_raw_frame(frame, self.piece_model, self.M)
      move = moves.detect_move(self.reference_occupied, current_occupied, self.current_board)

      if move:
        print(f"MOVE DETECTED on attempt {self.check_counter} -> {move.uci()}")
        self.current_board.push(move)
        self.reference_occupied = current_occupied
        self.latest_move = move.uci()
        self.is_checking_move = False

      elif self.check_counter >= self.MAX_CHECKS:
        print(f"Timed out. Tried {self.check_counter} times but found no legal move.")
        self.is_checking_move = False

    if self.show_piece_boxes:
      piece_results = self.piece_model(frame, conf=0.2, verbose=False, iou=0.2)
      display_frame = piece_results[0].plot(img=display_frame)

    return display_frame
  
  def _process_clock(self, frame):
    """Handles cropping the clock and running the clock YOLO model."""
    if self.clock_roi is None:
      return np.zeros((150, 600, 3), dtype=np.uint8)
    
    x, y, w, h = self.clock_roi
    x, y = max(0, x), max(0, y)
    clock_crop = frame[y:y+h, x:x+w]

    clock_results = self.clock_model(clock_crop, verbose=False)
    return clock_results[0].plot()
  
  def _send_to_gui(self, raw_frame, board_display, clock_display):
    """Manages the thread-safe queue."""
    if not self.frame_queue.empty():
      try:
        self.frame_queue.get_nowait()
      except queue.Empty:
        pass
    
    self.frame_queue.put({
      "frame": board_display,
      "clock_frame": clock_display,
      "raw_frame": raw_frame.copy(),
      "move": self.latest_move
    })

    if self.latest_move:
      self.latest_move = None