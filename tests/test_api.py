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
