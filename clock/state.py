class ClockState:
  """
  Tracks the game flow to determine which side is white.
  """
  def __init__(self):
    self.white_side = None # 'left' or 'right'

    # use helpers for different sides
    self.left_tracker = StableTimeTracker(required_consistency=8)
    self.right_tracker = StableTimeTracker(required_consistency=8)

  def process(self, current_left, current_right):
    """
    Takes the current times, compares them to history, 
    and returns a dictionary with identified white and black times.
    
    :param current_left: The current left time.
    :param current_right: The current right time.
    """
    # update tracker and check for changes
    left_changed = self.left_tracker.update(current_left)
    right_changed = self.right_tracker.update(current_right)

    # game logic, determine white if unknown
    if self.white_side is None:
      self._determine_side(left_changed, right_changed)

    # return formatted result
    return self._format_output()
  
  def _determine_side(self, left_changed, right_changed):
    """
    Decides who is white based on who moved first.
    """
    if left_changed and not right_changed:
      print("confirmed change on LEFT. left is white.")
      self.white_side = "left"
    elif right_changed and not left_changed:
      print("confirmed change on RIGHT. right is white.")
      self.white_side = "right"

  def _format_output(self):
    """
    Returns the dictionary expected.
    """
    # get the clean stable values from our trackers
    left_val = self.left_tracker.value
    right_val = self.right_tracker.value

    # handle calibrating state
    if left_val is None or right_val is None:
      return {"status": "calibrating", "left": "", "right": ""}
    
    # return mapped values if we know sides
    if self.white_side == "left":
      return {"status": "active", "white": left_val, "black": right_val}
    elif self.white_side == "right":
      return {"status": "active", "white": right_val, "black": left_val}
    
    # default waiting state
    return {"status": "waiting_for_move", "left": left_val, "right": right_val}
  
class StableTimeTracker:
  """
  Helper class that only updates its value if the input remains the same for N amount of frames.
  """
  def __init__(self, required_consistency=8):
    self.value = None # the currently confirmed stable value
    self.candidate = None # what we see right now
    self.consistency_count = 0 # how long we've seen it
    self.required = required_consistency

  def update(self, current_input):
    """
    Updates the tracker with a new reading.
    Returns True if the value changed this frame.
    
    :param current_input: The current value we just received.
    """
    # initialize if empty
    if self.value is None:
      self.value = current_input
      self.candidate = current_input
      return False
  
    # check candidate consistency
    if current_input == self.candidate:
      self.consistency_count += 1
    else:
      self.candidate = current_input
      self.consistency_count = 0

    # confirm change
    # only update the real value if we meet the consistency requirement
    if self.consistency_count >= self.required:
      if self.candidate != self.value and len(self.candidate) > 0:
        self.value = self.candidate
        return True
      
    return False
