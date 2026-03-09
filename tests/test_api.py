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