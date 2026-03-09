import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool

from  api.main import app, get_session, active_games

sqlite_url = "sqlite:///:memory:" # use in-memory db to make sure tests are fast and don't affect real db
engine = create_engine(
  sqlite_url,
  connect_args={"check_same_thread": False},
  poolclass=StaticPool
)

def get_session_override():
  with Session(engine) as session:
    yield session

# tell FastAPI to use override instead of the real database
app.dependency_overrides[get_session] = get_session_override

client = TestClient(app)

# ---- TEST SETUP AND TEARDOWN ----

@pytest.fixture(autouse=True)
def setup_and_teardown():
  # run before test:
  SQLModel.metadata.create_all(engine)
  active_games.clear()

  yield

  # runs after the tests:
  SQLModel.metadata.drop_all(engine)

# ---- TESTS ----
def test_set_and_get_live_game():
  """Test the in-memory active_games logic."""
  payload = {
    "board_id": 1,
    "fen": "startpos",
    "white_time": "10:00",
    "black_time": "10:00",
    "is_active": True
  }

  post_response = client.post("/api/update", json=payload)
  assert post_response.status_code == 200
  assert post_response.json() == { "status": "updated", "board_id": 1 }

  get_response = client.get("/api/game/1")
  assert get_response.status_code == 200
  assert get_response.json()["fen"] == "startpos"

def test_get_nonexistent_game():
  """Test the 404 error handler."""
  response = client.get("/api/game/999")
  assert response.status_code == 404
  assert "not found" in response.json()["detail"]

def test_set_and_get_player():
  """Test the database logic of creating and retreiving a player."""
  name = "Magnus Carlsen"
  payload = {"name": name}

  post_response = client.post("/api/players", json=payload)
  assert post_response.status_code == 200
  data = post_response.json()
  assert data["name"] == name
  assert data["id"] is not None

def test_prevent_duplicate_players():
  """Test that we get 400 error when trying to add duplicate player."""
  payload = {"name": "Hikaru Nakamura"}
  client.post("api/players", json=payload)
  
  response = client.post("api/players", json=payload)
  assert response.status_code == 400
  assert "eksisterer allerede" in response.json()["detail"]

# TODO: hva om man to ulike spillere har samme navn??

def test_get_new_player_profile():
  """Test fetching a newly created player with no games played."""
  name = "Vasily Smyslov"
  create_response = client.post("/api/players", json={"name": name})
  assert create_response.status_code == 200
  player_id = create_response.json()["id"]

  profile_response = client.get(f"/api/players/{player_id}")
  assert profile_response.status_code == 200

  data = profile_response.json()

  assert data["player"]["name"] == name
  assert data["player"]["id"] == player_id
  assert data["stats"]["total_games"] == 0
  assert data["stats"]["wins"] == 0
  assert data["stats"]["draws"] == 0
  assert data["stats"]["losses"] == 0

def test_player_stats_calculation():
  """Test that the dynamic stats calculator correctly counts game results."""
  p1 = client.post("/api/players", json={"name": "Magnus Carlsen"}).json()
  p2 = client.post("/api/players", json={"name": "Hikaru Nakamura"}).json()

  game_payload = {
    "white_player_name": p1["name"],
    "black_player_name": p2["name"],
    "white_player_id": p1["id"],
    "black_player_id": p2["id"],
    "result": "1-0",
    "pgn": "1. e4 e5"
  }
  archive_response = client.post("/api/archive", json=game_payload)
  assert archive_response.status_code == 200

  p1_profile = client.get(f"/api/players/{p1['id']}").json()

  assert p1_profile["stats"]["total_games"] == 1
  assert p1_profile["stats"]["wins"] == 1
  assert p1_profile["stats"]["draws"] == 0
  assert p1_profile["stats"]["losses"] == 0

  p2_profile = client.get(f"/api/players/{p2['id']}").json()

  assert p2_profile["stats"]["total_games"] == 1
  assert p2_profile["stats"]["wins"] == 0
  assert p2_profile["stats"]["draws"] == 0
  assert p2_profile["stats"]["losses"] == 1



def test_get_nonexistent_player():
  """Test fetching a player that doesn't exist."""
  response = client.get("/api/players/999")
  assert response.status_code == 404
  assert response.json()["detail"] == "Player not found"