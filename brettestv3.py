import cv2
import numpy as np
from ultralytics import YOLO
from collections import deque
from chessboard import chessboard
from moves import moves
import chess
import chess.pgn
import requests

# Last inn modellen og sett opp kamera
model = YOLO('brett.pt')
model2 = YOLO('brikker.pt')
cap = cv2.VideoCapture(0)
history = deque(maxlen=10)

# Variabler for å holde styr på tilstanden
current_board = chess.Board() # Lager en kopi av startoppsettet
reference_img = None
reference_occupied = []
M = None
M_inv = None
show_boxes = False #for og sjekke om modellen har funnet relevante hjørner
show_piece_boxes = False # Toggle for brikke-deteksjon

files = "abcdefgh"
ranks = "87654321"

print("SJAKK-DETEKSJON KLAR")
print(current_board)



while True:
    success, raw_frame = cap.read()
    if not success:
        break

    display_frame = raw_frame.copy()    

    #  Finn hjørner med YOLO, hvis perspektivet er låst kjøres ikke denne for og minimere steg i while løkken
    if M_inv is None or show_boxes:
        results = model(raw_frame, conf=0.05, verbose=False, iou=0.1)
        if show_boxes:
            display_frame = results[0].plot()

    if show_boxes:
        display_frame = results[0].plot()

    if len(results[0].boxes) >= 4:
        all_boxes = results[0].boxes.xyxy.cpu().numpy()
        confs = results[0].boxes.conf.cpu().numpy()
        best_indices = np.argsort(confs)[-4:]
        
        pts = []
        for i in best_indices:
            box = all_boxes[i]
            pts.append([(box[0] + box[2]) / 2, (box[1] + box[3]) / 2])
        
        history.append(chessboard.sort_points(pts))

    key = cv2.waitKey(1) & 0xFF

    #  'k' - Lås rutenettet (Perspektivet)
    if key == ord('k') and len(history) > 0:
        avg_corners = np.mean(history, axis=0).astype("float32")
        target_pts = np.float32([[0,0], [800,0], [800,800], [0,800]])
        M = cv2.getPerspectiveTransform(avg_corners, target_pts)
        M_inv = cv2.getPerspectiveTransform(target_pts, avg_corners)
        print(">> Brettet er låst i denne posisjonen!")

    #  Hvis låst, tegn og analyser

    #toggle boxer fra brett hjørne modellen av og på
    if key == ord('y'):
        show_boxes = not show_boxes
      

    #toggle boxer fra brikkemodell av og på
    if key == ord('u'):
        show_piece_boxes = not show_piece_boxes
        if not show_piece_boxes:
            try: cv2.destroyWindow("Brikke Deteksjon (Warped)")
            except: pass
        print(f">> Vis brikke-bokser: {show_piece_boxes}")

    if M_inv is not None:
        chessboard.draw_grid(display_frame, M_inv)
        
        # Lag et flatt bilde av brettet for analyse
        warped = cv2.warpPerspective(display_frame, M, (800, 800))
        gray_warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        
        # Hvis toggle er på, kjør model2 og vis resultatet
        if show_piece_boxes or key ==ord('l') or key == ord('s'):
            piece_results = model2(raw_frame, conf=0.2, verbose=False , iou=0.2)

        if show_piece_boxes:
            display_frame = piece_results[0].plot(img=display_frame)
        

        # 's' - Lagre bilde før du flytter brikke
        # To do : fikse slik at ikke modellen kjøres dobbelt.
        if key == ord('s'):
            reference_occupied = moves.get_occupied_squares_on_raw_frame(raw_frame, model2, M)
            print(f"Referanse lagret: {len(reference_occupied)} brikker funnet i original feed.")

        # 'l' - Sjekk hvilket trekk som er gjort
        # To do : fikse slik at ikke modellen kjøres dobbelt.
        if key == ord('l'):
            current_occupied = moves.get_occupied_squares_on_raw_frame(raw_frame, model2, M)
    
            # Finn ruter som har mistet en brikke
            moved_from = [r for r in reference_occupied if r not in current_occupied]
    
            # Finn ruter som har fått en brikke
            moved_to = [r for r in current_occupied if r not in reference_occupied]

            start_sq = None
            end_sq = None

            if len(moved_from) == 1 and len(moved_to) == 1:
                f_row, f_col = moved_from[0]
                t_row, t_col = moved_to[0]
                start_sq = f"{files[f_col]}{ranks[f_row]}"
                end_sq = f"{files[t_col]}{ranks[t_row]}"
                print(f"Trekk detektert: {start_sq} til {end_sq}")

            elif len(moved_from) == 1 and len(moved_to) == 0:
                f_row, f_col = moved_from[0]
                temp_start = f"{files[f_col]}{ranks[f_row]}"
        
                # Vi sjekker alle lovlige trekk fra start_sq og ser om 
                # destinasjonen er en rute som fortsatt er okkupert.
                possible_moves = [m for m in current_board.legal_moves if m.uci().startswith(temp_start)]
        
                for m in possible_moves:
                    dest_uci = m.uci()[2:4] 
                    d_col = files.find(dest_uci[0])
                    d_row = ranks.find(dest_uci[1])
            
                    if (d_row, d_col) in current_occupied:
                        start_sq = temp_start
                        end_sq = dest_uci

                #chessboard python biblotek implementasjon
            if start_sq and end_sq:
                move_string = start_sq + end_sq
                move = chess.Move.from_uci(move_string)    

                if move in current_board.legal_moves:
                    reference_occupied = moves.get_occupied_squares_on_raw_frame(raw_frame, model2, M)
                    print(f"Referanse lagret: {len(reference_occupied)} brikker funnet i original feed.")
                    current_board.push(move)
                    print(f"Trekk utført: {move_string}")
                    game = chess.pgn.Game.from_board(current_board)
                    print("\n--- OPPDATERT PGN ---")
                    print(game)
                    print("\n--- BRETT ---")
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
                    post_response = requests.post("http://127.0.0.1:8000/api/update", json=payload)
                    print(post_response)
                else:
                    print(f"Ulovlig trekk: {move_string}")

    
    cv2.imshow("Kamerabilde", display_frame)
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()