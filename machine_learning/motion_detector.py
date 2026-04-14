import cv2
import numpy as np

class MotionDetector:
  """
  Detects whan a hand enters and leaves the chessboard.
  """
  def __init__(self, movement_threshold=5000, required_still_frames=15):
    """
    movement_threshold: the number of pixels needing to change to count as motion
    
    required_still_frames: the number of frames of stillness before we trigger a move check
    """
    self.movement_threshold = movement_threshold
    self.required_still_frames = required_still_frames

    self.previous_frame = None
    self.is_moving = False
    self.still_counter = 0

  def update(self, warped_board_frame):
    """
    Takes a top-down, cropped image of the chessboard.
    Returns "MOTION", "SETTLED" or "IDLE".
    """
    # Convert to grayscale and blur to remove camera noise/flicker
    gray = cv2.cvtColor(warped_board_frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    # Initialize previous frame on first run
    if self.previous_frame is None:
      self.previous_frame = gray
      return "IDLE"
    
    # Calculate absoulte difference between the current frame and previous frame
    frame_delta = cv2.absdiff(self.previous_frame, gray)
    thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]

    # Count how many pixels changed
    motion_amount = cv2.countNonZero(thresh)

    # Update the previous frame for the next loop
    self.previous_frame = gray

    # Logic
    if motion_amount > self.movement_threshold:
      self.is_moving = True
      self.still_counter = 0
      return "MOTION"
    elif self.is_moving and motion_amount <= self.movement_threshold:
      # Motion has stopped, wait to be sure hand is gone
      self.still_counter += 1
      if self.still_counter >= self.required_still_frames:
        self.is_moving = False
        self.still_counter = 0
        return "SETTLED"
      
    return "IDLE"

  def reset(self):
    """Clears history."""
    self.previous_frame = None
    self.is_moving = False
    self.still_counter = 0