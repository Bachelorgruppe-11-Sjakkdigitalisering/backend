import requests
import threading

class ChessAPIClient:
  """Handles communication with the FastAPI backend asynchronously."""
  def __init__(self, endpoint="http://127.0.0.1:8000/api/update"):
    self.endpoint = endpoint

  def sync_game_state(self, payload: dict):
    """
    Takes the game data dictionary and sends it in a separate background thread.
    This makes sure the GUI neveer freezes while waiting for the network.
    """
    threading.Thread(target=self._post_data, args=(payload), daemon=True).start()

  def _post_data(self, payload):
    try:
      response = requests.post(self.endpoint, json=payload, timeout=5)

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