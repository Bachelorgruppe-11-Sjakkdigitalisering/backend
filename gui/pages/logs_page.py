import customtkinter as ctk

class LogPage(ctk.CTkFrame):
  """A dedicated page to view the entire log history of the session."""
  def __init__(self, parent, controller):
    super().__init__(parent, fg_color="transparent")
    self.controller = controller

    self.scroll_container = ctk.CTkScrollableFrame(self, label_text="Hele loggen")
    self.scroll_container.pack(fill="both", expand=True)
    
    self.colors = {
      "LOG": ("transparent"),
      "WARNING": ("#FFD580", "#CC7A00"),
      "ERROR": ("#FF9999", "#990000")
    }

  def render_all_logs(self, logs):
    """Clears the view and re-renders all logs from the logger memory."""
    for widget in self.scroll_container.winfo_children():
      widget.destroy()

    for entry in logs:
      self._render_log(entry)
      
  def on_new_log(self, entry):
    """
    Listens to new logs and makes sure UI is updated on main thread.
    """
    self.after(0, self._render_log, entry)

  def _render_log(self, entry):
    text = f"[{entry.timestamp}] {entry.message}"
    bg_color = self.colors.get(entry.level, ("transparent"))
    
    label = ctk.CTkLabel(self.scroll_container, text=text, fg_color=bg_color, anchor="w", justify="left", corner_radius=4)
    label.pack(fill="x", padx=2, pady=2)