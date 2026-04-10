import cv2
import numpy as np
import chess
import chess.pgn
import requests

FILES = "abcdefgh"
RANKS = "87654321"

#avhenger at modellen som kjøres har disse id-ene til respektive brikker
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
    results = model(frame, conf=0.3, verbose=False)
    occupied = {}
    
    if len(results[0].boxes) > 0:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        classes = results[0].boxes.cls.cpu().numpy()
        for box, cls in zip(boxes, classes):
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
                # Gjør om klasse-ID til farge.
                piece_color = COLOR_MAP.get(int(cls), "unknown") 
                occupied[(row, col)] = piece_color
                
    return occupied

def detect_castling(moved_from, moved_to, current_board):
    for move in current_board.legal_moves:
        if current_board.is_castling(move):
            return move
    return None

def detect_en_passant(moved_from, moved_to, current_board):
    for move in current_board.legal_moves:
        if current_board.is_en_passant(move):
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
    moved_to_empty = [pos for pos in current_occupied if pos not in reference_occupied]
    moved_to_changed = [pos for pos in current_occupied if pos in reference_occupied and current_occupied[pos] != reference_occupied[pos]]


    start_sq = None
    end_sq = None
    move = None

    # rokkade-sjekk
    if len(moved_from) == 2 and len(moved_to_empty) == 2:
        print("Sjekker rokade")
        move = detect_castling(moved_from, moved_to_empty, current_board)
        if move: 
            print("Fant rokade trekk og returnerer den")
            return move

    # en passant-sjekk
    elif len(moved_from) == 2 and len(moved_to_empty) == 1:
        print("Sjekker en passant")
        move = detect_en_passant(moved_from, moved_to_empty, current_board)
        if move: return move

    # vanlig trekk-sjekk altså flytte brikke til ledig felt
    if len(moved_from) == 1 and len(moved_to_empty) == 1:
        print("Sjekker vanlig trekk")
        f_row, f_col = moved_from[0]
        t_row, t_col = moved_to_empty[0]
        start_sq = f"{FILES[f_col]}{RANKS[f_row]}"
        end_sq = f"{FILES[t_col]}{RANKS[t_row]}"

    # vanlig capture-sjekk 
    elif len(moved_from) == 1 and len(moved_to_empty) == 0:
        print("Sjekker capture")
        f_row, f_col = moved_from[0]
        start_sq = f"{FILES[f_col]}{RANKS[f_row]}"
        
        # YOLO la merke til at brikken på destinasjonen byttet klasse
        if len(moved_to_changed) == 1:
            print("Scenario A")
            t_row, t_col = moved_to_changed[0]
            end_sq = f"{FILES[t_col]}{RANKS[t_row]}"
            
        # YOLO merket ikke at brikken byttet klasse (Fallback gjetting via python-chess)
        elif len(moved_to_changed) == 0:
            print("YOLO så ikke hvem som ble slått. Gjetter basert på lovlige trekk...")
            possible_captures = [m for m in current_board.legal_moves if m.uci().startswith(start_sq) and current_board.is_capture(m)]
            
            if len(possible_captures) == 1:
                return possible_captures[0]
            else:
                print("Klarte ikke å avgjøre capture automatisk (flere eller null mulige captures)")
                return None
        else:
            print(f"Feil: YOLO rapporterte at {len(moved_to_changed)} brikker byttet klasse samtidig. For mye støy.")
            return None
    if start_sq and end_sq:
        move_string = start_sq + end_sq
        #promoterings-sjekk
        print("Sjekker promotering")
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

