import threading
import queue
import cv2
import time
import numpy as np
import chessboard.chessboard as chessboard
from ultralytics import YOLO
from collections import deque

class VisionThread(threading.Thread):
  """
  Background thread that captures video and runs heavy AI models.
  Keeps the main GUI thread from freezing.
  """
  def __init__(self, frame_queue: queue.Queue, camera_source=0):
    super().__init__(daemon=True) # Daemon means this thread dies when the main app closes
    self.frame_queue = frame_queue
    self.camera_source = camera_source
    self.is_running = threading.Event()
    self.cap = None

    self.board_model = YOLO('brett.pt')
    self.clock_model = YOLO('klokke.pt')
    self.piece_model = YOLO('brikker100.pt')

    self.history = deque(maxlen=10)
    self.M = None
    self.M_inv = None
    self.show_boxes = True
    self.show_piece_boxes = True

    self.clock_roi = None

  def start_camera(self):
    self.cap = cv2.VideoCapture(self.camera_source)
    self.is_running.set()
    self.start() # Starts the run() method in the background

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

      processed_board_frame = frame.copy()
      clock_frame_to_display = None

      if self.M_inv is None or self.show_boxes:
        # Board is not locked
        results = self.board_model(frame, conf=0.05, verbose=False, iou=0.1)
        if self.show_boxes:
          processed_board_frame = results[0].plot()
        corners = chessboard.extract_corners(results)
        if corners is not None:
          self.history.append(corners)

      if self.M_inv is not None:
        # Board is locked
        chessboard.draw_grid(processed_board_frame, self.M_inv)
        piece_results = self.piece_model(frame, conf=0.2, verbose=False, iou=0.2)
        if self.show_piece_boxes:
          processed_board_frame = piece_results[0].plot(img=processed_board_frame)

      if self.clock_roi is not None:
        x, y, w, h = self.clock_roi
        x, y = max(0, x), max(0, y)

        clock_crop = frame[y:y+h, x:x+w]

        clock_results = self.clock_model(clock_crop, verbose=False)

        clock_frame_to_display = clock_results[0].plot()
        # TODO: hent siffer med ClockLogic og prosesser med ClockState
      else:
        clock_frame_to_display = np.zeros((150, 600, 3), dtype=np.uint8)

      # Pass data to GUI queue
      # Clear out old frames if the GUI is reading too slowly
      if not self.frame_queue.empty():
        try:
          self.frame_queue.get_nowait()
        except queue.Empty:
          pass
      
      # Put fresh frame into queue
      self.frame_queue.put({
        "frame": processed_board_frame,
        "clock_frame": clock_frame_to_display,
        "raw_frame": frame.copy()
      })

  def stop(self):
    """Safely shuts down the thread and camera."""
    self.is_running.clear()
    if self.cap:
      self.cap.release()