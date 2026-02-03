import cv2

class CameraStream:
  """
  Represents a camera stream. Only delivers the image.
  
  Takes an input of source for the camera. 
  This is an integer and defaults to 0 if no source is chosen.
  """
  def __init__(self, source=0):
    self.camera = cv2.VideoCapture(source)
    self.roi = None # (x, y, w, h) coordinates

    if not self.camera.isOpened():
      raise IOError("Unable to open camera.")
    
  def select_zoom_area(self):
    """
    Allows the user to select a region of interest (ROI).
    """
    success, first_frame = self.camera.read()
    if not success:
      print("Could not read frame for selection.")
      return
    
    # opens window to select area and deletes it after selection
    rect = cv2.selectROI("Select Area", first_frame, fromCenter=False, showCrosshair=True)
    cv2.destroyWindow("Select Area")
    cv2.waitKey(1)

    # check if a valid area was selected (width and height needs to be > 0)
    if rect[2] > 0 and rect[3] > 0:
      self.roi = (int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3]))

  def get_frame(self):
    """
    Returns (success, frame). 
    
    Crops frame if region of interest is set.
    """
    success, frame = self.camera.read()
    if not success:
      return success, None
    
    # if there is a region of interest, we crop to that region
    if self.roi:
      x, y, w, h = self.roi
      frame = frame[y:y+h, x: x+w]

    return success, frame
  
  def release(self):
    """
    Releases camera and destroys all windows this camera might have opened.
    """
    self.camera.release()
    cv2.destroyAllWindows()