import cv2

from camera import CameraStream
from vision import ObjectDetector
from clock.logic import ClockLogic
from clock.state import ClockState

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
  clock_state = ClockState()
  last_printed_times = None
  finished = False

  while not finished:
    success, frame = camera.get_frame()
    if not success:
      print("camera disconnected.")
      finished = True

    # get frame width
    h, w, _ = frame.shape

    # start detecting objects
    result = detector.detect(frame)

    # process logic
    # TODO: dette er nå spesifikt for å håndtere klokkelogikk, senere må vi håndtere annen logikk også
    raw_left, raw_right = ClockLogic.detections_to_time(result=result, frame_width=w)
    clock_info = clock_state.process(raw_left, raw_right)
    
    # display logic
    if clock_info["status"] == "active":
      # create a tuple of the current times
      current_times = (clock_info["white"], clock_info["black"])

      # only print if this tuple is different from the last one we saw
      if current_times != last_printed_times:
        print(f"white: {clock_info["white"]} | black: {clock_info["black"]}")
        last_printed_times = current_times
        # TODO: legg til api kall her i fremtiden
    elif clock_info["status"] == "waiting_for_move":
      print(f"waiting for first move...")
    
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