from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

# a shared base between live and archived games
class Game(SQLModel):
  """
  A shared data model for both archived games and live games to inherit from.
  """
  # names of players
  white_player_name: str = "White"
  black_player_name: str = "Black"
  # ids are optional in case of just a casual game with none registered players
  white_player_id: Optional[int] = Field(default=None, foreign_key="player.id")
  black_player_id: Optional[int] = Field(default=None, foreign_key="player.id")
  # full game pgn
  pgn: str = ""

# the live state model
class GameState(Game):
  """
  Represents a live game state.
  """
  board_id: int
  fen: str
  white_time: str
  black_time: str
  is_active: bool = True

# archived game database model
class ArchivedGame(Game, table=True):
  id: Optional[int] = Field(default=None, primary_key=True)
  date_played: datetime = Field(default_factory=datetime.now)
  result: str

# define player table
class Player(SQLModel, table=True):
  '''
  Represents a player with fields for an id and a name.
  '''
  id: Optional[int] = Field(default=None, primary_key=True)
  name: str = Field(index=True) # indexing makes searching by name much faster
  # kan evt ha mere detaljer om spillere her?
  # feks elo eller nasjonalitet hvis mulig