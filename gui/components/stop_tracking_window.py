import customtkinter as ctk

class StopTrackingWindow(ctk.CTkToplevel):
  """Popup to confirm stopping a game and optionally archiving the result."""
  def __init__(self, master, game_id: int, white_name: str, black_name: str, callback):
    super().__init__(master)
    self.callback = callback
    self.game_id = game_id

    self.title(f"Avslutt parti {game_id}")
    self.geometry("600x400")
    self.attributes("-topmost", True)
    self.grab_set() # Blocks interaction with main window

    self._build_ui(white_name, black_name)

  def _build_ui(self, white_name, black_name):
    # Headline
    ctk.CTkLabel(self, text=f"Avslutter sporing for: \n{white_name} vs {black_name}").pack(pady=(20, 10))

    # Result selection
    ctk.CTkLabel(self, text="Velg resultat:").pack()

    self.result_var = ctk.StringVar(value="Hvit seier")
    self.seg_button = ctk.CTkSegmentedButton(self, values=["Hvit seier", "Remis", "Svart seier"], variable=self.result_var)
    self.seg_button.pack(pady=(5, 20))

    # Buttons
    btn_frame = ctk.CTkFrame(self)
    btn_frame.pack(fill="x", padx=20)

    btn_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="button_group")

    # Cancel
    btn_cancel = ctk.CTkButton(
      btn_frame, text="Avbryt", fg_color="gray",
      command=lambda: self._close("cancel")
    )
    btn_cancel.grid(row=0, column=0, sticky="ew", padx=(0, 5))

    # Stop but don't save
    btn_discard = ctk.CTkButton(
      btn_frame, text="Stopp (Ikke lagre)", fg_color="#c93434", hover_color="#9e2a2a",
      command=lambda: self._close("discard")
    )
    btn_discard.grid(row=0, column=1, sticky="ew", padx=5)

    # Save to DB
    btn_save = ctk.CTkButton(
      btn_frame, text="Lagre i database", fg_color="#28a745", hover_color="#218838",
      command=lambda: self._close("save")
    )
    btn_save.grid(row=0, column=2, sticky="ew", padx=(5, 0))

  def _close(self, action: str):
    """Destroys the window and passes the decision back to the controller."""
    result = None
    match self.result_var.get():
      case "Hvit seier":
        result = "1-0"
      case "Remis":
        result = "1/2-1/2"
      case "Svart seier":
        result = "0-1"
      case _:
        result = None
    
    self.destroy()
    self.callback(self.game_id, action, result)