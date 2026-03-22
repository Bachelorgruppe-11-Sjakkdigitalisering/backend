import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk

class ROISelectorWindow(ctk.CTkToplevel):
  """A window that allows the admin to draw a rectangle over a static frame."""
  def __init__(self, master, pil_image, callback):
    super().__init__(master)
    self.title("Tegn rekatangel over klokka")
    self.callback = callback
    self.original_w, self.original_h = pil_image.size

    image = pil_image.resize((self.original_w, self.original_h))
    self.tk_image = ImageTk.PhotoImage(image)

    # Draw canvas
    self.canvas = tk.Canvas(self, width=self.original_w, height=self.original_h)
    self.canvas.pack()
    self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

    # Bind mouse events
    self.canvas.bind("<ButtonPress-1>", self.on_press)
    self.canvas.bind("<B1-Motion>", self.on_drag)
    self.canvas.bind("<ButtonRelease-1>", self.on_release)

    self.start_x = None
    self.start_y = None
    self.rect = None
    self.final_roi = None

    # Control panel
    self.btn_frame = ctk.CTkFrame(self)
    self.btn_frame.pack()

    self.btn_save = ctk.CTkButton(self.btn_frame, text="Lagre område", command=self.save_and_close, state="disabled")
    self.btn_save.pack(side="left")
    ctk.CTkButton(self.btn_frame, text="Avbryt", command=self.destroy).pack(side="left")

  def on_press(self, event):
    self.start_x = event.x
    self.start_y = event.y
    if self.rect:
      self.canvas.delete(self.rect)
    self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red", width=3)

  def on_drag(self, event):
    cur_x, cur_y = (event.x, event.y)
    self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

  def on_release(self, event):
    end_x, end_y = (event.x, event.y)

    x1 = min(self.start_x, end_x)
    y1 = min(self.start_y, end_y)
    x2 = max(self.start_x, end_x)
    y2 = max(self.start_y, end_y)

    w = x2 - x1
    h = y2 - y1

    self.final_roi = (int(x1), int(y1), int(w), int(h))
    self.btn_save.configure(state="normal")

  def save_and_close(self):
    if self.final_roi:
      self.callback(self.final_roi)
      self.destroy()