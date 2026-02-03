import cv2

from camera import CameraStream
from vision import ObjectDetector
from clock import ClockLogic

def main():
  # initialize our modules
  try:
    print("loading ai model...")
    # for now, specifically load clock model (CAN BE CHANGED TO PIECE MODEL IF PREFERRED)
    detector = ObjectDetector("klokke.pt")

    print ("loading camera...")
    camera = CameraStream(source=0)
    print("system initialized.")
  except Exception as e:
    print(f"error initializing: {e}")
    return

  # setup zoom area
  print("press enter to select zoom area")
  camera.select_zoom_area()

  # run main loop
  run(camera=camera, detector=detector)

def run(camera: CameraStream, detector: ObjectDetector):
  """
  Runs the main loop of the program.
  
  :param camera: The camera from which we capture the frames.
  :type camera: CameraStream
  :param detector: The detector for what we want to detect (for example clock or pieces).
  :type detector: ObjectDetector
  """
  finished = False
  while not finished:
    success, frame = camera.get_frame()
    if not success:
      print("camera disconnected.")
      finished = True

    # start detecting objects
    result = detector.detect(frame)

    # process logic
    # TODO: dette er nå spesifikt for å håndtere klokkelogikk, senere må vi håndtere annen logikk også
    current_time = ClockLogic.detections_to_time(result=result)
    
    if current_time:
      print(f"detected time: {current_time}")
      # TODO: i fremtiden send til api her (api.send_time(current_time) for eksempel)
    
    # visualize
    annotated_frame = result.plot()
    cv2.imshow("Clock Recognition", annotated_frame)

    # exit on 'q'
    if cv2.waitKey(1) == ord('q'):
      finished = True
    
  camera.release()

def initialize_modules():
  """
  Initializes the modules and returns the camera and detector.
  """
  try:
    print("loading ai model...")
    # for now, specifically load clock model (CAN BE CHANGED TO PIECE MODEL IF PREFERRED)
    detector = ObjectDetector("klokke.pt")

    print ("loading camera...")
    camera = CameraStream(source=0)
    print("system initialized.")
  except Exception as e:
    print(f"error initializing: {e}")
    return
  
  return detector, camera
  

if __name__ == "__main__":
  main()