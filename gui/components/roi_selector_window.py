import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk

class ROISelectorWindow(ctk.CTkToplevel):
  """A window that allows the admin to draw a rectangle over a static frame."""
  def __init__(self, master, pil_image, callback):
    super().__init__(master)
    self.title("Tegn rekatangel over klokka")
    self.callback = callback
    self.resizable(False, False)
    
    self.original_w, self.original_h = pil_image.size
    self.scale_factor = min(800 / self.original_w, 1.0)
    self.disp_w = int(self.original_w * self.scale_factor)
    self.disp_h = int(self.original_h * self.scale_factor)

    image = pil_image.resize((self.disp_w, self.disp_h), Image.Resampling.LANCZOS)
    self.tk_image = ImageTk.PhotoImage(image)

    self.grid_rowconfigure(0, weight=1)
    self.grid_rowconfigure(1, weight=0)
    self.columnconfigure(0, weight=1)

    # Canvas mathicng exact image size
    self.canvas = tk.Canvas(self, width=self.disp_w, height=self.disp_h, highlightthickness=0)
    self.canvas.grid(row=0, column=0, padx=10, pady=10)
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
    self.btn_frame.grid(row=1, column=0, sticky="ew")

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
    cur_x = max(0, min(event.x, self.disp_w))
    cur_y = max(0, min(event.y, self.disp_h))
    self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

  def on_release(self, event):
    end_x = max(0, min(event.x, self.disp_w))
    end_y = max(0, min(event.y, self.disp_h))

    scaled_x1 = min(self.start_x, end_x)
    scaled_y1 = min(self.start_y, end_y)
    scaled_w = max(self.start_x, end_x) - scaled_x1
    scaled_h = max(self.start_y, end_y) - scaled_y1

    # Map the scaled coordinates back to the original raw resolution
    orig_x = int(scaled_x1 / self.scale_factor)
    orig_y = int(scaled_y1 / self.scale_factor)
    orig_w = int(scaled_w / self.scale_factor)
    orig_h = int(scaled_h / self.scale_factor)

    if orig_w > 10 and orig_h > 10:
        self.final_roi = (orig_x, orig_y, orig_w, orig_h)
        self.btn_save.configure(state="normal")
    else:
        self.final_roi = None
        self.btn_save.configure(state="disabled")

  def save_and_close(self):
    if self.final_roi:
      self.callback(self.final_roi)
      self.destroy()