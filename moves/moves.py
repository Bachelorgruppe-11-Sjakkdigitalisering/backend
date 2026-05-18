import cv2
import numpy as np
import chess
import chess.pgn
import requests

# Constants for chessboard mapping.
FILES = "abcdefgh"
RANKS = "87654321"

#mapping class ID's from the YOLO model to their respective color.
COLOR_MAP = {
    0: "black", #  black-bishop
    1: "black", #  black-king
    2: "black", #  black-knight
    3: "black", #  black-pawn
    4: "black", #  black-queen
    5: "black", #  black-rook
    6: "white", #  white-bishop
    7: "white", #  white-king
    8: "white", #  white-knight
    9: "white", #  white-pawn
    10: "white", # white-queen
    11: "white"  # white-rook
}


def get_occupied_squares_on_raw_frame(frame, model, M):
    """Method for getting a overview over which fields on the board is covered by a chess piece.
    This returns a dictonary og occupied squares."""
    results = model(frame, conf=0.3, verbose=False)
    occupied = {}
    
    if len(results[0].boxes) > 0:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        classes = results[0].boxes.cls.cpu().numpy()
        for box, cls in zip(boxes, classes):
            # we use the bottom of the chess piece (px, py) because thats where the piece touches the board.
            h = box[3] - box[1] # høyden på boksen
            px = (box[0] + box[2]) / 2
            py = box[3] - (h * 0.10) # bottom center of the box + 10 % lift.
            
            # Transforms the point from camera perspective to the 800x800 view.
            point = np.array([[[px, py]]], dtype="float32")
            transformed_point = cv2.perspectiveTransform(point, M)[0][0]
            
            tx, ty = transformed_point[0], transformed_point[1]
            
            # Determine grid coordinates (0-7) based on the 800px scale (100px per square).
            col = int(tx // 100)
            row = int(ty // 100)
            
            # only record if the detected point falls within the 8x8 board boundary.
            if 0 <= col <= 7 and 0 <= row <= 7:
                piece_color = COLOR_MAP.get(int(cls), "unknown") 
                occupied[(row, col)] = piece_color
                
    return occupied

def get_board_diff(reference_occupied, current_occupied):
    """ compares the previous board state to the current. returns a list of coordiantes of lost, gained and changed pieces."""
    """Returnerer lister over felter som er mistet, vunnet eller endret."""
    lost = [pos for pos in reference_occupied if pos not in current_occupied]
    gained = [pos for pos in current_occupied if pos not in reference_occupied]
    changed = [pos for pos in current_occupied if pos in reference_occupied 
               and current_occupied[pos] != reference_occupied[pos]]
    return lost, gained, changed

def try_standard_move(lost, gained, changed, current_board):
    """Attempts to identify a standard move by checking all combinations of moves possible with the detected lost, gained and changed list."""
    from_candidates = lost
    to_candidates = gained + changed
    
    for f_row, f_col in from_candidates:
        for t_row, t_col in to_candidates:
            start_sq = f"{FILES[f_col]}{RANKS[f_row]}"
            end_sq = f"{FILES[t_col]}{RANKS[t_row]}"
            
            move = chess.Move.from_uci(start_sq + end_sq)
            if move in current_board.legal_moves:
                return move
            
            promo_move = chess.Move.from_uci(start_sq + end_sq + "q")
            if promo_move in current_board.legal_moves:
                return promo_move
    return None

def try_castling(lost, current_board):
    """checks if there is a legal castling move with the pieces detected."""
    for move in current_board.legal_moves:
        if current_board.is_castling(move):
            f_sq = chess.square_name(move.from_square)
           
            if any(f"{FILES[c]}{RANKS[r]}" == f_sq for r, c in lost):
                return move
    return None

def try_en_passant(lost, current_board):
    """checks if there is a legal en passant capture move with the pieces detected."""
    for move in current_board.legal_moves:
        if current_board.is_en_passant(move):
            f_sq = chess.square_name(move.from_square)
            if any(f"{FILES[c]}{RANKS[r]}" == f_sq for r, c in lost):
                return move
    return None

def detect_move(reference_occupied, current_occupied, current_board):
    """main move method which combines all of the special moves with the normal moves. Moves get detected by compared the current board state
    to the last confirmed board state. the method will check all possible combinations involving the fields that has changed,
    and determines what move are right by checking them against chess rule with python chess library."""

    lost, gained, changed = get_board_diff(reference_occupied, current_occupied)
    print(f"lost: {lost}, gained: {gained}, changed: {changed}")
    
    # if no move is detcted, assume no move was made.
    if not lost and not gained and not changed:
        return None

    # check for castling
    move = try_castling(lost, current_board)
    if move:
        return move
    
    # check for en passant  
    move = try_en_passant(lost, current_board)
    if move:
        return move
    
    #check for standard move
    move = try_standard_move(lost, gained, changed, current_board)
    if move:
        return move


    print("Endringer detektert, men ingen samsvarer med lovlige trekk.")
    return None