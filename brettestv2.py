import cv2
import numpy as np
from ultralytics import YOLO
from collections import deque
from board import board
from moves import moves

# Last inn modellen og sett opp kamera
model = YOLO('brett.pt')
cap = cv2.VideoCapture(0)
history = deque(maxlen=10)

# Variabler for å holde styr på tilstanden
current_board = [row[:] for row in moves.initial_board] # Lager en kopi av startoppsettet
reference_img = None
M = None
M_inv = None

print("SJAKK-DETEKSJON KLAR")
board.print_board(current_board)

show_boxes = False #for og sjekke om modellen har funnet relevante hjørner

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

    #toggle boxer fra modellen av og på
    if key == ord('y'):
        show_boxes = not show_boxes

    if M_inv is not None:
        board.draw_grid(frame, M_inv)
        
        # Lag et flatt bilde av brettet for analyse
        warped = cv2.warpPerspective(frame, M, (800, 800))
        gray_warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)

        # 's' - Lagre bilde før du flytter brikke
        if key == ord('s'):
            reference_img = gray_warped.copy()
            print(">> Referanse lagret. Flytt en brikke og trykk 'l'.")

        # 'l' - Sjekk hvilket trekk som er gjort
        if key == ord('l') and reference_img is not None:
            move = moves.detect_move(reference_img, gray_warped, current_board)
            if move:
                start_sq, end_sq = move
                print(f"** Trekk funnet: {start_sq} til {end_sq} **")
                
                # Finn indeksene og flytt brikken i matrisen
                c1, r1 = moves.files.find(start_sq[0]), 8 - int(start_sq[1])
                c2, r2 = moves.files.find(end_sq[0]), 8 - int(end_sq[1])
                
                piece = current_board[r1][c1]
                current_board[r2][c2] = piece
                current_board[r1][c1] = "."
                
                board.print_board(current_board)
                # Gjør det nåværende bildet til ny referanse
                reference_img = gray_warped.copy()
        
        
    
    cv2.imshow("Kamerabilde", frame)
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()