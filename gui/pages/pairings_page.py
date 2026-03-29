import customtkinter as ctk

class PairingsPage(ctk.CTkFrame):
  """
  Consists of a 2-column layout.
  On the left side the user can add new pairings, and on the right side there is a list of existing pairings.
  """
  def __init__(self, parent, controller):
    super().__init__(parent, fg_color="transparent")
    self.controller = controller

    # Configure 2-column layout
    self.grid_columnconfigure(0, weight=1)
    self.grid_columnconfigure(1, weight=2)
    self.grid_rowconfigure(0, weight=1)

    self._build_left_panel()
    self._build_right_panel()

  def _build_left_panel(self):
    self.left_panel = ctk.CTkFrame(self)
    self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

    ctk.CTkLabel(self.left_panel, text="Opprett et nytt par").pack(pady=(20,10))

    # White player inputs
    ctk.CTkLabel(self.left_panel, text="Hvit spiller (Fornavn / Etternavn / ID)").pack(anchor="w", padx=20)
    
    self.entry_white_first_name = ctk.CTkEntry(self.left_panel, placeholder_text="F.eks. Magnus")
    self.entry_white_first_name.pack(fill="x", padx=20, pady=(0, 5))
    
    self.entry_white_last_name = ctk.CTkEntry(self.left_panel, placeholder_text="F.eks. Carlsen")
    self.entry_white_last_name.pack(fill="x", padx=20, pady=(0, 5))
    
    self.entry_white_id = ctk.CTkEntry(self.left_panel, placeholder_text="Spiller ID (f.eks. 1)")
    self.entry_white_id.pack(fill="x", padx=20, pady=(0, 15))

    # Black player inputs
    ctk.CTkLabel(self.left_panel, text="Svart spiller (Fornavn / Etternavn / ID)").pack(anchor="w", padx=20)
    
    self.entry_black_first_name = ctk.CTkEntry(self.left_panel, placeholder_text="F.eks. Hikaru")
    self.entry_black_first_name.pack(fill="x", padx=20, pady=(0, 5))
    
    self.entry_black_last_name = ctk.CTkEntry(self.left_panel, placeholder_text="F.eks. Nakamura")
    self.entry_black_last_name.pack(fill="x", padx=20, pady=(0, 5))
    
    self.entry_black_id = ctk.CTkEntry(self.left_panel, placeholder_text="Spiller ID (f.eks. 2)")
    self.entry_black_id.pack(fill="x", padx=20, pady=(0, 15))

    # Camera for the pairing
    ctk.CTkLabel(self.left_panel, text="Kamera ID").pack(anchor="w", padx=20)
    
    self.entry_camera_id = ctk.CTkEntry(self.left_panel, placeholder_text="F.eks. 0")
    self.entry_camera_id.pack(fill="x", padx=20, pady=(0, 20))

    # Submit button
    self.btn_add = ctk.CTkButton(self.left_panel, text="Legg til par", command=self._on_add_clicked)
    self.btn_add.pack(padx=20, pady=10)

  def _build_right_panel(self):
    self.right_panel = ctk.CTkScrollableFrame(self, label_text="Aktive par")
    self.right_panel.grid(row=0, column=1, sticky="nsew")
    
    self.pairing_widgets = []

  def _on_add_clicked(self):
    """Gathers data from entries and sends it to the controller."""
    white_name = f"{self.entry_white_first_name.get().strip()} {self.entry_white_last_name.get().strip()}".strip()
    black_name = f"{self.entry_black_first_name.get().strip()} {self.entry_black_last_name.get().strip()}".strip()

    data = {
      "white_name": white_name,
      "white_id": self.entry_white_id.get().strip(),
      "black_name": black_name,
      "black_id": self.entry_black_id.get().strip(),
      "camera_id": self.entry_camera_id.get().strip()
    }
    self.controller.handle_new_pairing(data)

  def clear_inputs(self):
    """Clears the text fields after a successful add."""
    entries = [
        self.entry_black_first_name, self.entry_black_last_name, self.entry_black_id, 
        self.entry_white_first_name, self.entry_white_last_name, self.entry_white_id, 
        self.entry_camera_id
    ]
    for entry in entries:
      entry.delete(0, "end")

  def render_pairings_list(self, pairings_list):
    """Re-draws the list of pairings on the right side."""
    # Clear existing UI elements
    for widget in self.pairing_widgets:
      widget.destroy()
    self.pairing_widgets.clear()

    # Draw new elements based on the data by the controller
    for pairing in pairings_list:
      card = ctk.CTkFrame(self.right_panel)
      card.pack(fill="x", padx=10, pady=5)

      text = f"Kamera {pairing['camera_id']}: {pairing['white_name']} vs {pairing['black_name']}"
      
      label = ctk.CTkLabel(card, text=text)
      label.pack(side="left", padx=10, pady=10)

      # Add the card to our tracking list so we can delete it later
      self.pairing_widgets.append(card)