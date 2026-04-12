import customtkinter as ctk
import threading

class PlayerAutocomplete(ctk.CTkFrame):
  def __init__(self, master, api_client, on_player_selected, on_create_new):
    super().__init__(master, fg_color="transparent")
    self.api_client = api_client
    self.on_player_selected = on_player_selected
    self.on_create_new = on_create_new
    self.search_timer = None

    self.entry_search = ctk.CTkEntry(self, placeholder_text="Søk etter navn...")
    self.entry_search.pack(fill="x", pady=(0, 2))

    self.entry_search.bind("<KeyRelease>", self._schedule_search)

    self.dropdown_frame = ctk.CTkScrollableFrame(self, height=120)

  def _schedule_search(self, event):
    query = self.entry_search.get().strip()

    # Ignore search before user types more than two characters
    if len(query) < 2:
      self.dropdown_frame.pack_forget()
      return
    
    if self.search_timer:
      self.search_timer.cancel()

    # Debounce for 0.3s so we don't search on every input
    self.search_timer = threading.Timer(0.3, self._perform_search, args=[query])
    self.search_timer.start()

  def _perform_search(self, query):
    results = self.api_client.search_players_sync(query)
    self.after(0, self._update_dropdown, results, query)

  def _update_dropdown(self, results, query):
    # Clear old results
    for widget in self.dropdown_frame.winfo_children():
      widget.destroy()

    # Show dropdown
    self.dropdown_frame.pack(fill="x", pady=(0, 10))

    # Populate existing players
    if results:
      for player in results:
        btn_text = f"{player['name']} (ID: {player['id']})"
        btn = ctk.CTkButton(
          self.dropdown_frame,
          text=btn_text,
          anchor="w",
          # fg_color="transparent"
          command=lambda p=player: self._select_player(p)
        )
        btn.pack(fill="x", pady=2)

      # Separator between results and create new player button
      separator = ctk.CTkFrame(self.dropdown_frame, height=2, fg_color="gray")
      separator.pack(fill="x", padx=5, pady=5)

    # Permanent create new button
    btn_create = ctk.CTkButton(
      self.dropdown_frame,
      text=f"Opprett ny spiller: '{query}'",
      anchor="w",
      command=lambda: self._trigger_create(query)
    )
    btn_create.pack(fill="x", pady=2)

  def _select_player(self, player):
    self.dropdown_frame.pack_forget()
    self.entry_search.delete(0, "end")
    self.entry_search.insert(0, player['name'])
    self.on_player_selected(player)

  def _trigger_create(self, query):
    self.dropdown_frame.pack_forget()
    self.entry_search.delete(0, "end")
    self.entry_search.insert(0, query)
    self.on_create_new(query)