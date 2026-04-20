import requests
import threading

class ChessAPIClient:
  """Handles communication with the FastAPI backend asynchronously."""
  def __init__(self, logger, base_url="http://127.0.0.1:8000/api"):
    self.base_url = base_url
    self.logger = logger

  def search_players_sync(self, query:str) -> list:
    """
    Fetches players matching the search query.
    Runs synchronously to immediately return results to the UI thread.
    """
    try:
      response = requests.get(f"{self.base_url}/players", params={"search": query}, timeout=3)

      if response.status_code == 200:
        return response.json()
      else:
        self.logger.error(f"API Error: Klarte ikke hente spillere. Status: {response.status_code}")
        return []
      
    except requests.exceptions.Timeout:
      self.logger.error("API Error: Search request timed out.")
      return []
    except requests.exceptions.ConnectionError:
      self.logger.error("API Error: Tilkobling feilet.")
      return []
    except Exception as e:
      self.logger.error(f"API Error: Feil under spillersøk: {e}")
      return []
    
  def create_player_sync(self, name: str) -> dict:
    """
    Creates a new player in the database synchronously.
    Returns the created player dictionary or None on failure.
    """
    payload = {"name": name}

    try:
      response = requests.post(f"{self.base_url}/players", json=payload, timeout=3)
      if response.status_code == 200:
        return response.json()
      else:
        self.logger(f"API Error: Kunne ikke lage spiller. Status: {response.status_code}")
        return None
    except Exception as e:
      self.logger(f"API Error: Kunne ikke lage spiller: {e}")
      return None

  def sync_game_state(self, payload: dict):
    """
    Takes the game data dictionary and sends it in a separate background thread.
    This makes sure the GUI neveer freezes while waiting for the network.
    """
    threading.Thread(target=self._post_data, args=(payload,), daemon=True).start()

  def _post_data(self, payload):
    try:
      response = requests.post(f"{self.base_url}/update", json=payload, timeout=5)

      if response.status_code == 200:
        self.logger.log(f"API: Suksessfull sync. Server svarte: {response.json()}")
      else:
        self.logger.error(f"API Error: Server svarte: {response.status_code}: {response.text}")
      
    except requests.exceptions.Timeout:
      self.logger.error("API Error: Request timed out.")
    except requests.exceptions.ConnectionError:
      self.logger.error("API Error: Tilkobling feilet.")
    except Exception as e:
      self.logger.error(f"API Error: En uforventet feil oppstod: {e}")

  def archive_game_sync(self, payload: dict) -> bool:
    """
    Saves a finished game to the database synchronously.
    Payload should match the ArchivedGame model in FastAPI.
    """
    try:
      response = requests.post(f"{self.base_url}/archive", json=payload, timeout=3)
      if response.status_code == 200:
        self.logger.log(f"API: Parti lagret i arkivet! {response.json()}")
        return True
      else:
        self.logger.error(f"API Error: Kunne ikke lagre parti. Status: {response.status_code}")
        return False
    except Exception as e:
      self.logger.error(f"API Error under lagring av parti: {e}")
      return False

  def remove_live_game_sync(self, board_id: int):
    """
    Tells the backend to remove this game from the active live feed.
    """
    try:
      response = requests.delete(f"{self.base_url}/game/{board_id}")
      if response.status_code == 200:
        self.logger.log(f"API: Parti {board_id} fjernet fra live-feeden på nettsiden.")
      else:
        self.logger.warning(f"API Advarsel: Fikk status {response.status_code} ved fjerning av live-parti.")
    except Exception as e:
      self.logger.error(f"API Error: Kunne ikke kontakte server for å fjerne live-parti: {e}")