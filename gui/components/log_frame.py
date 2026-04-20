import customtkinter as ctk

class LogFrame(ctk.CTkScrollableFrame):
  def __init__(self, master, max_display=50, **kwargs):
    super().__init__(master, **kwargs)
    self.max_display = max_display
    self.log_labels = []

    # Color map (light mode, dark mode)
    self.colors = {
      "LOG": ("transparent"),
      "WARNING": ("#FFD580", "#CC7A00"), # Orange
      "ERROR": ("#FF9999", "#990000")    # Red
    }

  def on_new_log(self, entry):
    """
    Callback from SessionLogger.
    Uses .after(0, ...) to make sure the GUI is updated on the main thread.
    """
    self.after(0, self._render_log, entry)

  def _render_log(self, entry):
    text = f"[{entry.timestamp}] {entry.message}"
    bg_color = self.colors.get(entry.level, ("transparent"))

    label = ctk.CTkLabel(self, text=text, fg_color=bg_color, anchor="w", justify="left", corner_radius=4)
    label.pack(fill="x", padx=2, pady=2)

    self.log_labels.append(label)

    # Cap amount of UI elements to prevent lag
    if len(self.log_labels) > self.max_display:
      old_label = self.log_labels.pop(0)
      old_label.destroy()

    # Auto-scroll to the bottom
    self._parent_canvas.yview_moveto(1.0)
