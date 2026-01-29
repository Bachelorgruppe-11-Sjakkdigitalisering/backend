import cv2
from ultralytics import YOLO

# load model
model = YOLO('klokke.pt')

# opens the camera
camera = cv2.VideoCapture(0)

if not camera.isOpened():
  print("unable to open camera. will exit. bye.")
  exit()

# take one picture to select zoom area
success, first_frame = camera.read()
if success:
  # opens window to drag mouse to select clock
  rect = cv2.selectROI("choose zoom area", first_frame, fromCenter=False, showCrosshair=True)
  cv2.destroyWindow("choose zoom area")

  # rect returns (x, y, w, h). if w or h is 0, user didn't select anything
  if rect[2] == 0 or rect[3] == 0:
    zoom_active = False
  else:
    zoom_active = True
    x,y,w,h = int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])
else:
  exit()

while True:
  # read camera feed
  success, frame = camera.read()

  # if unable to read camera, exit loop
  if not success:
    print("can't receive frame. exiting...")
    break

  # apply zoom
  if zoom_active:
    # we slice the array to create a new, smaller image containing the clock
    frame = frame[y:y+h, x:x+w]

  # feed camera to yolo model and get the results as a list
  results = model(frame, verbose=False)

  # visualize results with boxes and labels on the image
  annotated_frame = results[0].plot()

  # display annotated frame
  cv2.imshow("Episk ultra mega sjakk kamera", annotated_frame)

  # wait for q to be pressed to exit loop
  if cv2.waitKey(1) == ord('q'):
    break

# exit everything when out of loop
camera.release()
cv2.destroyAllWindows()
