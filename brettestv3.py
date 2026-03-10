import cv2
import numpy as np
from ultralytics import YOLO
from collections import deque
from board import board
from moves import moves
import chess

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
    if M_inv is None:
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
        
        history.append(board.sort_points(pts))

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
        board.draw_grid(display_frame, M_inv)
        
        # Lag et flatt bilde av brettet for analyse
        warped = cv2.warpPerspective(display_frame, M, (800, 800))
        gray_warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        
        # Hvis toggle er på, kjør model2 og vis resultatet
        if show_piece_boxes or key ==ord('l') or key == ord('s'):
            piece_results = model2(raw_frame, conf=0.2, verbose=False , iou=0.04)
            print(f"Antall brikker funnet: {len(piece_results[0].boxes)}")

        if show_piece_boxes:
            display_frame = piece_results[0].plot()
        

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

            if len(moved_from) == 1 and len(moved_to) == 1:
                f_row, f_col = moved_from[0]
                t_row, t_col = moved_to[0]
                start_sq = f"{files[f_col]}{ranks[f_row]}"
                end_sq = f"{files[t_col]}{ranks[t_row]}"
                print(f"Trekk detektert: {start_sq} til {end_sq}")
        
                # Oppdater matrisen din her...
                reference_occupied = current_occupied

            
        
        
    
    cv2.imshow("Kamerabilde", display_frame)
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()