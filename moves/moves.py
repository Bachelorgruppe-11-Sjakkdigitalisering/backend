import cv2
import numpy as np
import chess
import chess.pgn
import requests

FILES = "abcdefgh"
RANKS = "87654321"


def get_occupied_squares_on_raw_frame(frame, model, M):
    results = model(frame, conf=0.3, verbose=False)
    occupied = []
    
    if len(results[0].boxes) > 0:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        for box in boxes:
            # Vi bruker bunnen av boksen (px, py) fordi det er der brikken 
            # faktisk berører brettet.
            h = box[3] - box[1] # høyden på boksen
            px = (box[0] + box[2]) / 2
            py = box[3] - (h * 0.10) # senter av bunnen av brikken + 10 % reisning
            
            # Transformer punktet fra kamera-koordinater til 800x800 systemet
            point = np.array([[[px, py]]], dtype="float32")
            transformed_point = cv2.perspectiveTransform(point, M)[0][0]
            
            tx, ty = transformed_point[0], transformed_point[1]
            
            # Finn kolonne og rad (0-7) i 800x800 rutenettet
            col = int(tx // 100)
            row = int(ty // 100)
            
            if 0 <= col <= 7 and 0 <= row <= 7:
                occupied.append((row, col))
                
    return list(set(occupied))

def detect_castling(moved_from, moved_to, current_board):
    for move in current_board.legal_moves:
        if current_board.is_castling(move):
            start_sq = chess.square_name(move.from_square)
            end_sq = chess.square_name(move.to_square)
            
            if start_sq in moved_from and end_sq in moved_to:
                return move
    return None

def detect_en_passant(moved_from, moved_to, current_board):
    for move in current_board.legal_moves:
        if current_board.is_en_passant(move):
            start_sq = chess.square_name(move.from_square)
            end_sq = chess.square_name(move.to_square)
            
            if start_sq in moved_from and end_sq in moved_to:
                return move
    return None

def check_promotion(move_string, current_board):
 
    promo_move_q = chess.Move.from_uci(move_string + "q")
    if promo_move_q in current_board.legal_moves:
        # Standardiserer til å alltid promotere til Dronning inntil videre.
        return promo_move_q
    return None

def detect_move (reference_occupied, current_occupied, current_board):
    moved_from = [r for r in reference_occupied if r not in current_occupied]
    moved_to = [r for r in current_occupied if r not in reference_occupied]

    start_sq = None
    end_sq = None
    move = None

    # rokkade-sjekk
    if len(moved_from) == 2 and len(moved_to) == 2:
        move = detect_castling(moved_from, moved_to, current_board)
        if move: return move

    # en passant-sjekk
    elif len(moved_from) == 2 and len(moved_to) == 1:
        move = detect_en_passant(moved_from, moved_to, current_board)
        if move: return move

    # vanlig trekk-sjekk altså flytte brikke til ledig felt
    if len(moved_from) == 1 and len(moved_to) == 1:
        f_row, f_col = moved_from[0]
        t_row, t_col = moved_to[0]
        start_sq = f"{FILES[f_col]}{RANKS[f_row]}"
        end_sq = f"{FILES[t_col]}{RANKS[t_row]}"

    # vanlig capture-sjekk 
    elif len(moved_from) == 1 and len(moved_to) == 0:
        f_row, f_col = moved_from[0]
        temp_start = f"{FILES[f_col]}{RANKS[f_row]}"
        
        possible_moves = [m for m in current_board.legal_moves if m.uci().startswith(temp_start)]
        for m in possible_moves:
            dest_uci = m.uci()[2:4] 
            d_col = FILES.find(dest_uci[0])
            d_row = RANKS.find(dest_uci[1])
            if (d_row, d_col) in current_occupied:
                start_sq = temp_start
                end_sq = dest_uci

    if start_sq and end_sq:
        move_string = start_sq + end_sq
        #promoterings-sjekk
        promoted_move = check_promotion(move_string, current_board)
        if promoted_move:
            return promoted_move
        
        move = chess.Move.from_uci(move_string)
        if move in current_board.legal_moves:
            return move
        else:
            print(f"Ulovlig trekk forsøkt: {move_string}")
            return None
    return None

def execute_move (move, current_board):
    current_board.push(move)
    print(f"Trekk utført: {move.uci()}")
    game = chess.pgn.Game.from_board(current_board)
    print("Den oppdaterte PGN filen")
    print(game)
    print("Aktivt brett:")
    print(current_board)
    payload = {
        "board_id": 1,
        "white_player_name": "Herman Lundby-Holen",
        "black_player_name": "Dennis Johansen",
        "fen": current_board.fen(),
        "pgn": str(game),
        "white_time": "10:00",
        "black_time": "10:00",
        "is_active": True
    }
    try: 
        post_response = requests.post("http://127.0.0.1:8000/api/update", json=payload)
        print(f"API Respons: {post_response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Kunne ikke koble til API: {e}")