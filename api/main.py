from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from sqlmodel import Session, select
from typing import List

from api.database import ArchivedGame, create_db_and_tables, get_session

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

# defines the data shape
class GameState(BaseModel):
  board_id: int
  fen: str
  white_time: str
  black_time: str
  is_active: bool = True

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
  print(f"saved game to db: {game.white_player} vs {game.black_player}")
  return game

@app.get("/api/archive/search", response_model=List[ArchivedGame])
async def search_games(player: str = None, session: Session = Depends(get_session)):
  '''
  Searches for a game or gets all of them
  '''
  query = select(ArchivedGame)

  if player:
    # search for the name in wither white or black player columns
    query = query.where(
      (ArchivedGame.white_player.contains(player)) |
      (ArchivedGame.black_player.contains(player))
    )
  
  # order by newest first
  query = query.order_by(ArchivedGame.date_played.desc())

  results = session.exec(query).all()
  return results

# Run with: uvicorn api.main:app --reload --port 8000