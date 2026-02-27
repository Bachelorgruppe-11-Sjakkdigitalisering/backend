from fastapi import FastAPI
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
  fen: str
  white_time: str
  black_time: str
  is_active: bool = True

# global variable to store state in memory
# we initialize it with the starting chess position
current_game = {
    "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "white_time": "10:00",
    "black_time": "10:00",
    "is_active": True
}

# endpoint for pushing new game state data
@app.post("/api/update")
async def set_game_state(data: GameState):
  # 'global' here tells python that we want to update the 'current_game' variable outside of this method,
  # not create a new current_game variable inside of it
  global current_game
  # '.model_dump()' converts the data from a Pydantic Object to a standard python dictionary
  current_game = data.model_dump()
  print(f"Updates received: {current_game['fen'][:15]}...")
  return {"status": "updated"}

# this endpoint will be used by react to fetch game state in future
@app.get("/api/state")
async def get_game_state():
  return current_game

# Run with: uvicorn api.main:app --reload --port 8000