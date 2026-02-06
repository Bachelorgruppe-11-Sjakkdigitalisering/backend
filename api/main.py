from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# global variable to store state in memory
# we initialize it with the starting chess position
current_game = {
    "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "white_time": "10:00",
    "black_time": "10:00",
    "is_active": True
}

# create an endpoing for getting the data
# this endpoint will be used by react to fetch game state in future
@app.get("/api/state")
async def get_game_state():
  return current_game

# Run with: uvicorn api.main:app --reload --port 8000