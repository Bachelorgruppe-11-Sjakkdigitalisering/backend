import cv2
import numpy as np
from ultralytics import YOLO
from collections import deque
from board import board
from moves import moves

# Last inn modellen og sett opp kamera
model = YOLO('brett.pt')
model2 = YOLO('brikker100.pt')
cap = cv2.VideoCapture(0)
history = deque(maxlen=10)

# Variabler for å holde styr på tilstanden
current_board = [row[:] for row in moves.initial_board] # Lager en kopi av startoppsettet
reference_img = None
reference_occupied = []
M = None
M_inv = None
show_boxes = False #for og sjekke om modellen har funnet relevante hjørner
show_piece_boxes = False # Toggle for brikke-deteksjon

files = "abcdefgh"
ranks = "87654321"

print("SJAKK-DETEKSJON KLAR")
board.print_board(current_board)



while True:
    success, frame = cap.read()
    if not success:
        break

    #  Finn hjørner med YOLO
    results = model(frame, conf=0.05, verbose=False, iou=0.1)

    if show_boxes:
        frame = results[0].plot()

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
        board.draw_grid(frame, M_inv)
        
        # Lag et flatt bilde av brettet for analyse
        warped = cv2.warpPerspective(frame, M, (800, 800))
        gray_warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        
        #for og teste om modellen er bedre uten warped bilde
        display_frame = frame.copy()

        # Hvis toggle er på, kjør model2 og vis resultatet
        if show_piece_boxes:
            piece_results = model2(warped, conf=0.1, verbose=False)
            print(f"DEBUG: Model2 ser {len(piece_results[0].boxes)} brikker. Beste conf: {piece_results[0].boxes.conf.max().item() if len(piece_results[0].boxes) > 0 else 0:.2f}")
            warped_vis = piece_results[0].plot()
            
            cv2.imshow("Brikke Deteksjon (Warped)", warped_vis)
        else:
            # Lukk vinduet hvis det er åpent og vi skrur av toggle
            if cv2.getWindowProperty("Brikke Deteksjon (Warped)", cv2.WND_PROP_VISIBLE) > 0:
                cv2.destroyWindow("Brikke Deteksjon (Warped)")

        # 's' - Lagre bilde før du flytter brikke
        if key == ord('s'):
            reference_occupied = moves.get_occupied_squares(warped, model2)
            print(f"Referanse lagret: {len(reference_occupied)} brikker funnet.")

        # 'l' - Sjekk hvilket trekk som er gjort
        if key == ord('l'):
            current_occupied = moves.get_occupied_squares(warped, model2)
    
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

            
        
        
    
    cv2.imshow("Kamerabilde", frame)
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()