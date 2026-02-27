from sqlmodel import SQLModel, Field, create_engine, Session
from datetime import datetime
from typing import Optional

# define database table
class ArchivedGame(SQLModel, table=True):
  '''
  Represents an archived game
  '''
  id: Optional[int] = Field(default=None, primary_key=True)
  tournament_name: str = "Turneringsnavn"
  date_played: datetime = Field(default_factory=datetime.now)

  # player info
  white_player: str
  black_player: str
  result: str # 1-0 | 0-1 | 1/2

  # the actual game
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