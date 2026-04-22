import re

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

  @staticmethod
  def parse_to_seconds(raw_string: str, reference_seconds: int | None = None) -> int | None:
    """
    Converts raw YOLO string to seconds. 
    Uses a reference time to find out difference between hh:mm and mm:ss for 3 and 4 digit displays.
    Includes a check to drop impossible YOLO hallucinations.
    """
    if not raw_string:
      return None
    
    # Strip everything that isn't a digit
    clean_string = re.sub(r'\D', '', raw_string)
    if not clean_string:
      return None
    
    length = len(clean_string)
    parsed_seconds = None

    try:
      if length >= 5:
        # 5+ digits is always H:MM:SS
        parsed_seconds = (int(clean_string[:-4]) * 3600) + (int(clean_string[-4:-2]) * 60) + int(clean_string[-2:])
      
      elif length == 3 or length == 4:
        # Could be H:MM or MM:SS
        val_1 = int(clean_string[:-2]) # Hours or Minutes
        val_2 = int(clean_string[-2:]) # Minutes or Seconds

        option_hh_mm = (val_1 * 3600) + (val_2 * 60)
        option_mm_ss = (val_1 * 60) + val_2

        if reference_seconds is None:
          parsed_seconds = option_hh_mm if option_hh_mm >= 3600 else option_mm_ss
        else:
          diff_hh_mm = abs(reference_seconds - option_hh_mm)
          diff_mm_ss = abs(reference_seconds - option_mm_ss)
          parsed_seconds = option_hh_mm if diff_hh_mm < diff_mm_ss else option_mm_ss
      
      else:
        # 1 or 2 digits is always seconds
        parsed_seconds = int(clean_string)

      if reference_seconds is not None and parsed_seconds is not None:
        # If the YOLO reading jumps by more than 3600 seconds it has probably hallucinated. Drop the frame.
        if abs(parsed_seconds - reference_seconds) > 3600:
          return None
        
      return parsed_seconds
      
    except ValueError:
      return None