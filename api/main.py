from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# starts a local FastAPI server
app = FastAPI()

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

# Run with: uvicorn api.main:app --reload --port 8000