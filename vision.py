from ultralytics import YOLO

class ObjectDetector:
  """
  A wrapper for the YOLO logic.

  Generic so it can be used for all types of recognition without changing the code, just the model path.
  """
  def __init__(self, model_path):
    # load the specific model
    self.model = YOLO(model_path)

  def detect(self, frame):
    """
    Runs the model on the given frame and returns the result object.
    
    :param frame: The frame to run the model on.
    """
    # verbose=False keeps the console clean
    results = self.model(frame, verbose=False, iou=0.7)
    return results[0]