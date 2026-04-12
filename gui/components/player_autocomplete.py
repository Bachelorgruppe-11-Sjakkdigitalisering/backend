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
    print(f"{query}")