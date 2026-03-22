import customtkinter as ctk

class LiveFeedWindow(ctk.CTkToplevel):
  """
  A popup window that displays the main board feed and a cropped clock feed.
  """
  def __init__(self, master):
    super().__init__(master)

    self.title("Live kamera feed")
    self.geometry("700x700")

    self._build_ui()

  def _build_ui(self):
    self.grid_rowconfigure(0, weight=3)
    self.grid_rowconfigure(1, weight=1)
    self.grid_columnconfigure(0, weight=1)

    # Main board feed label
    self.board_frame = ctk.CTkFrame(self)
    self.board_frame.grid(row=0, column=0, sticky="nsew")
    self.board_frame.pack_propagate(False)
    
    self.board_label = ctk.CTkLabel(self.board_frame, text="Loading board feed...")
    self.board_label.pack(expand=True, fill="both")

    # Clock cutout feed label
    self.clock_frame = ctk.CTkFrame(self)
    self.clock_frame.grid(row=1, column=0, sticky="nsew")
    self.clock_frame.pack_propagate(False)

    self.clock_label = ctk.CTkLabel(self.clock_frame, text="Loading clock feed...")
    self.clock_label.pack(expand=True, fill="both")

  def update_feeds(self, board_image: ctk.CTkImage, clock_image: ctk.CTkImage):
    """Updates the board and clock frames."""
    if board_image:
      self.board_label.configure(image=board_image, text="")
    if clock_image:
      self.clock_label.configure(image=clock_image, text="")