import requests
import threading

class ChessAPIClient:
  """Handles communication with the FastAPI backend asynchronously."""
  def __init__(self, base_url="http://127.0.0.1:8000/api"):
    self.base_url = base_url

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
        print(f"API Error: Failed to fetch players. Status: {response.status_code}")
        return []
      
    except requests.exceptions.Timeout:
      print("API Error: Search request timed out.")
      return []
    except requests.exceptions.ConnectionError:
      print("API Error: Connection refused. Is FastAPI running on port 8000?")
      return []
    except Exception as e:
      print(f"API Error during player search: {e}")
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
        print(f"API Error: Could not create player. Status: {response.status_code}")
        return None
    except Exception as e:
      print(f"API Error during player creation: {e}")
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
        print(f"API: Sync successful. Server responded: {response.json()}")
      else:
        print(f"API Error: Server returned status {response.status_code}: {response.text}")
      
    except requests.exceptions.Timeout:
      print("API Error: Request timed out. Is the FastAPI server running?")
    except requests.exceptions.ConnectionError:
      print("API Error: Connection refused. Make sure uvicorn is running on port 8000")
    except Exception as e:
      print(f"API Error: An unexpected error occured: {e}")

  def archive_game_sync(self, payload: dict) -> bool:
    """
    Saves a finished game to the database synchronously.
    Payload should match the ArchivedGame model in FastAPI.
    """
    try:
      response = requests.post(f"{self.base_url}/archive", json=payload, timeout=3)
      if response.status_code == 200:
        print(f"API: Parti lagret i arkivet! {response.json()}")
        return True
      else:
        print(f"API Error: Kunne ikke lagre parti. Status: {response.status_code}")
        return False
    except Exception as e:
      print(f"API Error under lagring av parti: {e}")
      return False
