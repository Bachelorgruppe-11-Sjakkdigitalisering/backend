import threading
import queue
import cv2
import time

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

  def start_camera(self):
    self.cap = cv2.VideoCapture(self.camera_source)
    self.is_running.set()
    self.start() # Starts the run() method in the background

  def run(self):
    """The main loop running in the background thread."""
    while self.is_running.is_set():
      if not self.cap or not self.cap.isOpened():
        time.sleep(0.1)
        continue

      success, frame = self.cap.read()
      if not success:
        continue

      # TODO: legg til YOLO her

      processed_frame = frame.copy()

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