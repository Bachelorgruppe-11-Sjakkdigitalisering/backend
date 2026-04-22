import customtkinter as ctk
from gui.components.player_autocomplete import PlayerAutocomplete 

class PairingsPage(ctk.CTkFrame):
  """
  Consists of a 2-column layout.
  On the left side the user can add new pairings, and on the right side there is a list of existing pairings.
  """
  def __init__(self, parent, controller):
    super().__init__(parent, fg_color="transparent")
    self.controller = controller

    # State for players
    self.selected_players = {
      "white": {"id": None, "name": None, "widget": None},
      "black": {"id": None, "name": None, "widget": None}
    }

    # Configure 2-column layout
    self.grid_columnconfigure(0, weight=9, uniform="layout")
    self.grid_columnconfigure(1, weight=11, uniform="layout")
    self.grid_rowconfigure(0, weight=1)

    self._build_left_panel()
    self._build_right_panel()

  def _build_left_panel(self):
    self.left_panel = ctk.CTkScrollableFrame(self, label_text="Opprett et nytt par")
    self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

    # White player inputs
    ctk.CTkLabel(self.left_panel, text="Hvit spiller").pack(anchor="w", padx=20)
    self.selected_players["white"]["widget"] = PlayerAutocomplete(
      self.left_panel,
      api_client=self.controller.api_client, 
      on_player_selected=lambda player: self._on_player_selected("white", player),
      on_create_new=lambda name: self._on_player_create_new("white", name)
    )
    self.selected_players["white"]["widget"].pack(fill="x", padx=20, pady=(0, 15))

    # Black player inputs
    ctk.CTkLabel(self.left_panel, text="Svart spiller").pack(anchor="w", padx=20)
    self.selected_players["black"]["widget"] = PlayerAutocomplete(
      self.left_panel, 
      api_client=self.controller.api_client, 
      on_player_selected=lambda player: self._on_player_selected("black", player),
      on_create_new=lambda name: self._on_player_create_new("black", name)
    )
    self.selected_players["black"]["widget"].pack(fill="x", padx=20, pady=(0, 15))  

    # Camera for the pairing
    ctk.CTkLabel(self.left_panel, text="Kamera ID").pack(anchor="w", padx=20)
    self.entry_camera_id = ctk.CTkEntry(self.left_panel, placeholder_text="F.eks. 0")
    self.entry_camera_id.pack(fill="x", padx=20, pady=(0, 20))

    # Time control
    ctk.CTkLabel(self.left_panel, text="Tidskontroll (starttid)").pack(anchor="w", padx=20)
    self.time_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
    self.time_frame.pack(fill="x", padx=20, pady=(0, 20))
    self.time_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="time_cols")
    # Hours
    self.entry_hours = ctk.CTkEntry(self.time_frame, placeholder_text="Timer (f.eks 1)")
    self.entry_hours.grid(row=0, column=0, padx=(0, 5), sticky="ew")
    # Minutes
    self.entry_minutes = ctk.CTkEntry(self.time_frame, placeholder_text="Minutter (f.eks 30)")
    self.entry_minutes.grid(row=0, column=1, padx=5, sticky="ew")
    # Seconds
    self.entry_seconds = ctk.CTkEntry(self.time_frame, placeholder_text="Sekunder (f.eks 0)")
    self.entry_seconds.grid(row=0, column=2, padx=(5, 0), sticky="ew")


    # Submit button
    self.btn_add = ctk.CTkButton(self.left_panel, text="Legg til par", command=self._on_add_clicked)
    self.btn_add.pack(padx=20, pady=10)

  def _build_right_panel(self):
    self.right_panel = ctk.CTkScrollableFrame(self, label_text="Aktive par")
    self.right_panel.grid(row=0, column=1, sticky="nsew")
    
    self.pairing_widgets = []

  def _on_player_selected(self, color, player_data):
    """Callback for when a user selects a player from the dropdown."""
    self.selected_players[color]["id"] = player_data['id']
    self.selected_players[color]["name"] = player_data['name']
    self.controller.logger.log(f"{color} spiller valgt: {player_data['name']}")

  def _on_player_create_new(self, color, player_name):
    """Pops up a confirmation dialog before creating a new player."""
    # Create popup window
    dialog = ctk.CTkToplevel(self)
    dialog.title("Bekreft ny spiller")
    dialog.geometry("350x150")
    dialog.attributes("-topmost", True) # Keeps it on top
    dialog.grab_set() # Blocks interaction with main window until answered

    # Center text
    ctk.CTkLabel(
      dialog, 
      text=f"Er du sikker på at du vil opprette\n en ny spiller med navnet:\n\n'{player_name}'?"
    ).pack(pady=(20, 25), padx=(20, 25))

    def on_confirm():
      dialog.destroy()
      # Call API to create new player
      new_player = self.controller.api_client.create_player_sync(player_name)

      if new_player:
        self.selected_players[color]["id"] = new_player['id']
        self.selected_players[color]["name"] = new_player['name']
        self.controller.logger.log(f"Opprettet og valgte {color} spiller: {new_player['name']} (ID: {new_player['id']})")
      else:
        self.controller.logger.error("ERROR: Kunne ikke opprette spilleren")

    def on_cancel():
      dialog.destroy()
      # Clear search box
      self.selected_players[color]["widget"].entry_search.delete(0, "end")
      self.selected_players[color]["id"] = None
      self.selected_players[color]["name"] = None

    btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_frame.pack(fill="x", padx=20)

    ctk.CTkButton(btn_frame, text="Avbryt", command=on_cancel).pack(side="left", padx=10, expand=True)
    ctk.CTkButton(btn_frame, text="Opprett", command=on_confirm).pack(side="right", padx=10, expand=True)


  def _on_add_clicked(self):
    """Gathers data from entries and sends it to the controller."""
    white = self.selected_players["white"]
    black = self.selected_players["black"]

    if not white["id"] or not black["id"]:
      self.controller.logger.warning("Advarsel: Du må velge både hvit og svart spiller!")
      return
    
    # Parse time inputs
    try:
      hour_str = self.entry_hours.get().strip()
      minute_str = self.entry_minutes.get().strip()
      second_str = self.entry_seconds.get().strip()

      hours = int(hour_str) if hour_str else 0
      minutes = int(minute_str) if minute_str else 0
      seconds = int(second_str) if second_str else 0

      initial_seconds = (hours * 3600) + (minutes * 60) + seconds

      if initial_seconds <= 0:
        self.controller.logger.warning("Advarsel: Tidskontrollen må være større enn 0 sekunder hvis du vil bruke klokka.")
        return
      
    except ValueError:
      self.controller.logger.error("Tidskontroll Error: Vennligst bruk kun tall for tidskontrollen.")
      return

    data = {
      "white_name": white["name"],
      "white_id": white["id"],
      "black_name": black["name"],
      "black_id": black["id"],
      "camera_id": self.entry_camera_id.get().strip(),
      "initial_seconds": initial_seconds
    }
    self.controller.handle_new_pairing(data)

  def clear_inputs(self):
    """Clears the text fields and resets state after a successful add."""
    # Clear the custom autocomplete text boxes
    self.selected_players["white"]["widget"].entry_search.delete(0, "end")
    self.selected_players["black"]["widget"].entry_search.delete(0, "end")
    
    # Clear camera and time
    self.entry_camera_id.delete(0, "end")
    self.entry_hours.delete(0, "end")
    self.entry_minutes.delete(0, "end")
    self.entry_seconds.delete(0, "end")
    
    # Reset internal state
    for color in ["white", "black"]:
      self.selected_players[color]["id"] = None
      self.selected_players[color]["name"] = None

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

      card.grid_columnconfigure(0, weight=1)
      card.grid_columnconfigure(1, weight=0)

      text = f"Kamera {pairing['camera_id']}: {pairing['white_name']} vs {pairing['black_name']}"
      label = ctk.CTkLabel(card, text=text, anchor="w")
      label.grid(row=0, column=0, sticky="w", padx=10, pady=10)

      btn_frame = ctk.CTkFrame(card, fg_color="transparent")
      btn_frame.grid(row=0, column=1, sticky="e", padx=10, pady=10)

      if pairing.get("status") != "active":
        # Start game
        btn_start = ctk.CTkButton(
          btn_frame,
          text="Start tracking",
          command=lambda game_id=pairing['game_id']: self.controller.start_tracking_game(game_id)
        )
        btn_start.pack(side="left", padx=(0, 5))

        # Remove game
        btn_delete = ctk.CTkButton(
          btn_frame,
          text="Slett",
          fg_color="#c93434", hover_color="#9e2a2a", width=60,
          command=lambda game_id=pairing['game_id']: self.controller.remove_pairing(game_id)
        )
        btn_delete.pack(side="left")
      else:
        status_label = ctk.CTkLabel(card, text="Aktiv", text_color="green")
        status_label.grid(row=0, column=1, sticky="e", padx=10, pady=10)

      # Add the card to our tracking list so we can delete it later
      self.pairing_widgets.append(card)