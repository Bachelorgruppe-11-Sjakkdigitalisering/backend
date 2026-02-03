class ClockLogic:
  """
  Contains the logic for the clock.

  This includes:
  - Sorting detections from left to right.
  - Splitting the time strings into whites time and blacks time.
  """
  @staticmethod
  def detections_to_time(result, frame_width):
    """
    Takes raw YOLO results, extracts boxes, sorts them by x-coordinate, and returns two strings of numbers, one for the left side and one for the right side.
    
    :param result: The raw YOLO results.
    :param frame_width: The width of the fram from which we will calculate the midpoint to split clock into left and right side.
    """
    boxes = result.boxes
    
    left_digits = []
    right_digits = []
    midpoint = frame_width / 2 # use the middle of the clock (roi user selected) to split the sides

    # extract info from each box
    for box in boxes:
      class_id = int(box.cls[0])

      # use the models internal names map to extract the "names" of the numbers
      label_name = result.names[class_id]

      # calculate x position for sorting
      coords = box.xyxy[0].tolist()
      x_center = (coords[0] + coords[2]) / 2

      # sort into left and right side
      if x_center < midpoint:
        left_digits.append((x_center, label_name))
      else:
        right_digits.append((x_center, label_name))

    # sort each side from left to right
    left_digits.sort(key=lambda x: x[0])
    right_digits.sort(key=lambda x: x[0])

    # join into strings and return the sides
    time_left = "".join([d[1] for d in left_digits])
    time_right = "".join([d[1] for d in right_digits])
        
    return time_left, time_right