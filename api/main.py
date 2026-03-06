from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlmodel import Session, select
from typing import List
from sqlalchemy import or_

from api.database import create_db_and_tables, get_session
from api.models import GameState, ArchivedGame, Player

@asynccontextmanager
async def lifespan(app: FastAPI):
  # everything before yield runs on startup
  print("starting up...")
  print("creating database tables...")
  create_db_and_tables()

  yield # the application runs on this pause

  # everything after yield runs on shutdown
  print("shutting down and cleaning up...")

# pass lifespan function to fastapi app
app = FastAPI(lifespan=lifespan)

# ALLOWS REACT TO TALK TO PYTHON (CORS)
# React runs on localhost:5173, FastAPI on localhost:8000. 
# Browsers block this by default unless you add this:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev, allow everyone. Lock this down later.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# global variable to store state in memory
active_games: dict[int, dict] = {}

# endpoint for pushing new game state data
@app.post("/api/update")
async def set_game_state(data: GameState):
  # '.model_dump()' converts the data from a Pydantic Object to a standard python dictionary
  active_games[data.board_id] = data.model_dump()
  print(f"Updates received for board {data.board_id}: FEN={data.fen}")
  return {"status": "updated", "board_id": data.board_id}

# endpoint to fetch a specific game
@app.get("/api/game/{board_id}")
async def get_game_state(board_id: int):
  # check if board exists in memory
  if board_id not in active_games:
    raise HTTPException(status_code=404, detail=f"Board {board_id} not found or started yet.")
  # return game if found
  return active_games[board_id]

# endpoint to list all active games
@app.get("/api/games")
async def list_games():
  return active_games

# --- DATABASE ENDPOINTS ---
@app.post("/api/archive", response_model=ArchivedGame)
async def save_game(game: ArchivedGame, session: Session = Depends(get_session)):
  '''
  Saves a finished game to the database.
  '''
  session.add(game)
  session.commit()
  session.refresh(game)
  print(f"saved game to db: {game.white_player_name} vs {game.black_player_name}")
  return game

@app.get("/api/archive/search", response_model=List[ArchivedGame])
async def search_games(player: str = None, session: Session = Depends(get_session)):
  '''
  Searches for a game or gets all of them
  '''
  query = select(ArchivedGame)

  if player:
    # search for the name in either white or black player columns
    query = query.where(
      (ArchivedGame.white_player_name.contains(player)) |
      (ArchivedGame.black_player_name.contains(player))
    )
  
  # order by newest first
  query = query.order_by(ArchivedGame.date_played.desc())

  results = session.exec(query).all()
  return results

@app.get("/api/archive/{game_id}", response_model=ArchivedGame)
async def get_archived_game(game_id: int, session: Session = Depends(get_session)):
  """
  Fetches a single archived game by its database ID.
  """
  game = session.get(ArchivedGame, game_id)

  if not game:
    raise HTTPException(status_code=404, detail="Game not found")
  
  return game

@app.get("/api/players", response_model=List[Player])
async def list_players(search: str = None, session: Session = Depends(get_session)):
  """
  Fetches all registered players, optionally filtered by name.
  """
  query = select(Player)

  if search: 
    query = query.where(Player.name.contains(search))

  query = query.order_by(Player.name)
  return session.exec(query).all()

@app.get("/api/players/{player_id}")
async def get_player_profile(player_id: int, session: Session = Depends(get_session)):
  """
  Fetches a single player and returns the player together with their stats.
  """
  player = session.get(Player, player_id)
  if not player:
    raise HTTPException(status_code=404, detail="Player not found")
  
  # calculate stats dynamically
  games_as_white = session.exec(select(ArchivedGame).where(ArchivedGame.white_player_id == player_id)).all()
  games_as_black = session.exec(select(ArchivedGame).where(ArchivedGame.black_player_id == player_id)).all()

  wins = 0
  draws = 0
  losses = 0

  for game in games_as_white:
    if game.result == "1-0": wins += 1
    elif game.result == "1/2-1/2": draws += 1
    else: losses += 1

  for game in games_as_black:
    if game.result == "0-1": wins += 1
    elif game.result == "1/2-1/2": draws += 1
    else: losses += 1

  return {
    "player": player,
    "stats": {
      "total_games": len(games_as_white) + len(games_as_black),
      "wins": wins,
      "draws": draws,
      "losses": losses
    }
  }

@app.get("/api/players/{player_id}/games")
async def get_player_games(player_id: int, session: Session = Depends(get_session)):
  """
  Fetches all games played by a specific player.
  """
  # find all games where this player was either white or black
  query = select(ArchivedGame).where(
    or_(ArchivedGame.white_player_id == player_id, ArchivedGame.black_player_id == player_id)
  ).order_by(ArchivedGame.date_played.desc())

  return session.exec(query).all()

@app.post("/api/players", response_model=Player)
async def create_player(player: Player, session: Session = Depends(get_session)):
  """
  Creates a new player in the database.
  """
  # safety check to see if a plyer with this name already exists
  existing_player = session.exec(select(Player).where(Player.name == player.name)).first()

  if existing_player:
    raise HTTPException(
      status_code=400,
      detail=f"En spiller med navnet '{player.name}' eksisterer allerede i databasen"
    )
  
  # save the new player
  session.add(player)
  session.commit()
  session.refresh(player)

  print(f"Ny spiller lagt til: {player.name} (ID: {player.id})")
  return player

# Run with: python -m uvicorn api.main:app --reload --port 8000   