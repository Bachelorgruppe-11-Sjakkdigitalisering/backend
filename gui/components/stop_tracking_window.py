import customtkinter as ctk

class StopTrackingWindow(ctk.CTkToplevel):
  """Popup to confirm stopping a game and optionally archiving the result."""
  def __init__(self, master, game_id: int, white_name: str, black_name: str, callback):
    super().__init__(master)
    self.callback = callback
    self.game_id = game_id

    self.title(f"Avslutt parti {game_id}")
    self.geometry("400x400")
    self.attributes("-topmost", True)
    self.grab_set() # Blocks interaction with main window

    self._build_ui(white_name, black_name)

  def _build_ui(self, white_name, black_name):
    # Headline
    ctk.CTkLabel(self, text=f"Avslutter sporing for: \n{white_name} vs {black_name}").pack(pady=(20, 10))

    # Result selection
    ctk.CTkLabel(self, text="Velg resultat:").pack()

    self.result_var = ctk.StringVar(value="1-0")
    self.seg_button = ctk.CTkSegmentedButton(self, values=["1-0", "1/2-1/2", "0-1"], variable=self.result_var)
    self.seg_button.pack(pady=(5, 20))

    # Buttons
    btn_frame = ctk.CTkFrame(self)
    btn_frame.pack(fill="x", padx=20)

    # Cancel
    ctk.CTkButton(
      btn_frame, text="Avbryt", fg_color="gray",
      command=lambda: self._close("cancel")
    ).pack(side="left", padx=5)

    # Stop but don't save
    ctk.CTkButton(
      btn_frame, text="Stopp (Ikke lagre)", fg_color="#c93434", hover_color="#9e2a2a",
      command=lambda: self._close("discard")
    ).pack(side="left", padx=5)

    # Save to DB
    ctk.CTkButton(
      btn_frame, text="Lagre i database", fg_color="#28a745", hover_color="#218838",
      command=lambda: self._close("save")
    ).pack(side="right", padx=5)

  def _close(self, action: str):
    """Destroys the window and passes the decision back to the controller."""
    result = self.result_var.get() if action == "save" else None
    self.destroy()
    self.callback(self.game_id, action, result)