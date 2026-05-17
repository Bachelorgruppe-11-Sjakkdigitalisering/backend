import pytest
import chess
from moves import (
  get_board_diff,
  try_castling,
  try_en_passant,
  try_standard_move,
  detect_move,
)

# Fixtures

@pytest.fixture
def standard_board():
  """Returns a standard starting chess board."""
  return chess.Board()

# Logic tests

@pytest.mark.parametrize("reference, current, model_lost, model_gained, model_changed", [
  # A piece moved from (6,4) to (4,4) (means e2 to e4)
  (
    {(6,4): "white"},
    {(4,4): "white"},
    [(6,4)], [(4,4)], []
  ),
  # A piece was captured. White moves to (2,2), Black at (2,2) is gone.
  (
    {(4,2): "white", (2,2): "black"},
    {(2,2): "white"},
    [(4,2)], [], [(2,2)]
  ),
  # No changes
  (
    {(0,0): "black"},
    {(0,0): "black"},
    [], [], []
  ),
  # Empty boards
  ({},{},[],[],[]),
])
def test_get_board_diff(reference, current, model_lost, model_gained, model_changed):
  """Tests if differences between two board states are calculated correctly."""
  lost, gained, changed = get_board_diff(reference, current)

  assert set(lost) == set(model_lost)
  assert set(gained) == set(model_gained)
  assert set(changed) == set(model_changed)

def test_try_standard_move_valid(standard_board):
  """Tests detection of a standard e2-24 pawn move."""
  lost = [(6,4)] # e2
  gained = [(4,4)] #e4
  changed = []

  move = try_standard_move(lost, gained, changed, standard_board)
  assert move is not None
  assert move == chess.Move.from_uci("e2e4")

def test_try_standard_move_promotion():
  "Tests pawn promotion logic."
  # Board with a pawn on e7 ready to promote
  board = chess.Board("8/4P3/8/8/8/8/8/8 w - - 0 1")
  lost = [(1,4)] # e7
  gained = [(0,4)] # e8
  changed = []

  move = try_standard_move(lost, gained, changed, board)
  assert move is not None
  assert move == chess.Move.from_uci("e7e8q")

def test_try_castling():
  """Tests kingside castling detection."""
  # Board where kingside castle is legal
  board = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
  lost = [(7,4), (7,7)] # King on e1, rook on h1 lost

  move = try_castling(lost, board)
  assert move is not None
  assert move == chess.Move.from_uci("e1g1")

def test_try_en_passant():
  """Tests en passant capture detection."""
  # Board where en passant is legal
  board = chess.Board("rnbqkbnr/pppp1ppp/8/3Pp3/8/8/PPP1PPPP/RNBQKBNR w KQkq e6 0 1")
  # White pawn moves d5e6, capturing black pawn on e5
  lost = [(3,3)]

  move = try_en_passant(lost, board)
  assert move is not None
  assert move == chess.Move.from_uci("d5e6")

# Integration tests

def test_detect_move_no_change(standard_board):
  """Tests the full detect_move method when no moves are made."""
  reference = {(6,4): "white"}
  current = {(6,4): "white"}

  move = detect_move(reference, current, standard_board)
  assert move is None

def test_detect_move_valid(standard_board):
  """Tests the full detect_move method with a valid standard move."""
  reference = {(6,4): "white"}
  current = {(4,4): "white"}

  move = detect_move(reference, current, standard_board)
  assert move is not None
  assert move == chess.Move.from_uci("e2e4")