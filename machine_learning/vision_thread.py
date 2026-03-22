import threading
import queue
import cv2
import time
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

    self.history = deque(maxlen=10)
    self.M = None
    self.M_inv = None
    self.show_boxes = True

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

  def run(self):
    """The main loop running in the background thread."""
    while self.is_running.is_set():
      if not self.cap or not self.cap.isOpened():
        time.sleep(0.1)
        continue

      success, frame = self.cap.read()
      if not success:
        continue

      processed_frame = frame.copy()

      if self.M_inv is None or self.show_boxes:
        # Board is not locked
        results = self.board_model(frame, conf=0.05, verbose=False, iou=0.1)

        if self.show_boxes:
          processed_frame = results[0].plot()

        corners = chessboard.extract_corners(results)
        if corners is not None:
          self.history.append(corners)

      if self.M_inv is not None:
        # Board is locked
        chessboard.draw_grid(processed_frame, self.M_inv)

      # Pass data to GUI queue
      # Clear out old frames if the GUI is reading too slowly
      if not self.frame_queue.empty():
        try:
          self.frame_queue.get_nowait()
        except queue.Empty:
          pass
      
      # Put fresh frame into queue
      self.frame_queue.put({
        "frame": processed_frame
      })

  def stop(self):
    """Safely shuts down the thread and camera."""
    self.is_running.clear()
    if self.cap:
      self.cap.release()