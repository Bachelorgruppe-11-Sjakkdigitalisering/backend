class ClockState:
  """
  Tracks the game flow to determine which side is white.
  """
  def __init__(self):
    self.white_side = None # 'left' or 'right'

    # the "confirmed" stable time from the past
    self.stable_left = None
    self.stable_right = None

    # the "candidate time" (what we currently see but aren't sure of yet)
    self.candidate_left = None
    self.candidate_right = None

    # amount of frames the candidate has held steady
    self.consistency_left = 0
    self.consistency_right = 0

    # the required amount of frames for a move on the clock to be valid
    self.required_consistency = 8

  def process(self, current_left, current_right):
    """
    Takes the current times, compares them to history, 
    and returns a dictionary with identified white and black times.
    
    :param current_left: The current left time.
    :param current_right: The current right time.
    """
    # initialize history if it's the first run
    if self.stable_left is None:
      self.stable_left = current_left
      self.stable_right = current_right
      self.candidate_left = current_left
      self.candidate_right = current_right
      return {
        "status": "calibrating",
        "left": current_left,
        "right": current_right
      }
    
    # check for stability on the left
    if current_left == self.candidate_left:
      self.consistency_left += 1
    else:
      # it flickered, reset counter and pick new candidate
      self.candidate_left = current_left
      self.consistency_left = 0

    # check for stability on the right
    if current_right == self.candidate_right:
      self.consistency_right += 1
    else:
      self.candidate_right = current_right
      self.consistency_right = 0

    # determine if a real change has happened
    left_has_changed_for_real = False
    if self.consistency_left >= self.required_consistency:
      if self.candidate_left != self.stable_left and len(self.candidate_left) > 0:
        left_has_changed_for_real = True
        self.stable_left = self.candidate_left
    
    right_has_changed_for_real = False
    if self.consistency_right >= self.required_consistency:
      if self.candidate_right != self.stable_right and len(self.candidate_right) > 0:
        right_has_changed_for_real = True
        self.stable_right = self.candidate_right

    # game logic
    if self.white_side is None:
      if left_has_changed_for_real and not right_has_changed_for_real:
        print("confirmed change on LEFT. left is white.")
        self.white_side = "left"
      elif right_has_changed_for_real and not left_has_changed_for_real:
        print("confirmed change on RIGHT. right is white.")
        self.white_side = "right"

    # return result
    if self.white_side == "left":
      return {
        "status": "active",
        "white": self.stable_left,
        "black": self.stable_right
      }
    elif self.white_side == "right":
      return {
        "status": "active",
        "white": self.stable_right,
        "black": self.stable_left
      }
    
    return {
      "status": "waiting_for_move",
      "left": self.stable_left,
      "right": self.stable_right
    }