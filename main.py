import cv2

# opens the camera
camera = cv2.VideoCapture(0)

if not camera.isOpened():
  print("unable to open camera. will exit. bye.")
  exit()

while True:
  # read camera feed
  success, frame = camera.read()

  # if unable to read camera, exit loop
  if not success:
    print("can't receive frame. exiting...")
    break

  # display frame
  cv2.imshow("Episk ultra mega sjakk kamera", frame)

  # wait for q to be pressed to exit loop
  if cv2.waitKey(1) == ord('q'):
    break

# exit everything when out of loop
camera.release()
cv2.destroyAllWindows()
