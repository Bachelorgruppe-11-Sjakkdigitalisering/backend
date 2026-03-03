from sqlmodel import SQLModel, Field, create_engine, Session
from datetime import datetime
from typing import Optional

# define player table
class Player(SQLModel, table=True):
  '''
  Represents a player with fields for an id and a name.
  '''
  id: Optional[int] = Field(default=None, primary_key=True)
  name: str = Field(index=True) # indexing makes searching by name much faster
  # kan evt ha mere detaljer om spillere her?
  # feks elo eller nasjonalitet hvis mulig

# define archived game database table
class ArchivedGame(SQLModel, table=True):
  '''
  Represents an archived game with id, tournament name, date played, who white player was,
  who black player was, the result, and a pgn.
  '''
  id: Optional[int] = Field(default=None, primary_key=True)
  tournament_name: str = "Turneringsnavn"
  date_played: datetime = Field(default_factory=datetime.now)

  # player info
  white_player_id: int = Field(foreign_key="player.id")
  black_player_id: int = Field(foreign_key="player.id")
  white_player_name: str
  black_player_name: str

  # game info
  result: str # 1-0 | 0-1 | 1/2
  pgn: str

# create sqlite engine
# creates a file named "chess_archive.db"
sqlite_file_name = "chess_archive.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# the engine bridges python and sqlite file
engine = create_engine(sqlite_url, echo=True)

def create_db_and_tables():
  '''
  Helper function to create the tables of the database
  '''
  SQLModel.metadata.create_all(engine)

def get_session():
  '''
  Helper function to get a database session
  '''
  with Session(engine) as session:
    yield session