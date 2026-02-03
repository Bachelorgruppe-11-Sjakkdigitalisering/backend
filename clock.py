class ClockLogic:
  """
  Contains the logic for the clock.

  This includes:
  - Sorting detections from left to right.
  - Splitting the time strings into whites time and blacks time.
  """
  @staticmethod
  def detections_to_time(result):
    """
    Takes raw YOLO results, extracts boxes, sorts them by x-coordinate, and returns a string of numbers.
    
    :param result: The raw YOLO results.
    """
    boxes = result.boxes
    detections = []

    # extract info from each box
    for box in boxes:
      class_id = int(box.cls[0])

      # use the models internal names map to extract the "names" of the numbers
      label_name = result.names[class_id]

      # calculate x position for sorting
      coords = box.xyxy[0].tolist()
      x_center = (coords[0] + coords[2]) / 2

      # save coordinate together with the label
      detections.append((x_center, label_name))

    # sort from left to right
    detections.sort(key=lambda x: x[0])

    # TODO: kanskje endre linja under til mer komplisert logikk for å faktisk skille mellom svarts og hvits tid??
    # join into a single string
    return "".join([d[1] for d in detections])