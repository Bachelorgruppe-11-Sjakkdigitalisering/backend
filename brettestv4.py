import cv2
from ultralytics import YOLO
from collections import deque
import chess
import chessboard  
import moves       

# Last inn modellene
model = YOLO('brett.pt')
model2 = YOLO('brikker.pt')
cap = cv2.VideoCapture(0)

history = deque(maxlen=10)
current_board = chess.Board()

reference_occupied = []
M = None
M_inv = None

show_boxes = False
show_piece_boxes = False

print("SJAKK-DETEKSJON KLAR")
print(current_board)

while True:
    success, raw_frame = cap.read()
    if not success:
        break

    display_frame = raw_frame.copy()    
    key = cv2.waitKey(1) & 0xFF

    # Finn hjørner hvis ikke låst, eller hvis show_boxes er på
    if M_inv is None or show_boxes:
        results = model(raw_frame, conf=0.05, verbose=False, iou=0.1)
        if show_boxes:
            display_frame = results[0].plot()
        
        corners = chessboard.extract_corners(results)
        if corners is not None:
            history.append(corners)

    # Håndter tastetrykk
    if key == ord('k'): # Lås brett
        M, M_inv = chessboard.lock_perspective(history)
        if M is not None:
            print(">> Brettet er låst i denne posisjonen!")

    elif key == ord('y'): # Toggle brett-bokser
        show_boxes = not show_boxes

    elif key == ord('u'): # Toggle brikke-bokser
        show_piece_boxes = not show_piece_boxes
        print(f">> Vis brikke-bokser: {show_piece_boxes}")

    elif key == ord('s') and M is not None: # Lagre referansebilde
        reference_occupied = moves.get_occupied_squares_on_raw_frame(raw_frame, model2, M)
        print(f"Referanse lagret: {len(reference_occupied)} brikker funnet i original feed.")

    elif key == ord('l') and M is not None: # Gjør et trekk
        current_occupied = moves.get_occupied_squares_on_raw_frame(raw_frame, model2, M)
        move = moves.detect_move(reference_occupied, current_occupied, current_board)
        
        if move:
            moves.execute_and_broadcast_move(move, current_board)
            # Oppdater referansen automatisk etter et gyldig trekk
            reference_occupied = moves.get_occupied_squares_on_raw_frame(raw_frame, model2, M)
            print(f"Ny referanse autolagret: {len(reference_occupied)} brikker.")

    # Tegn brikker og rutenett hvis brettet er låst
    if M_inv is not None:
        chessboard.draw_grid(display_frame, M_inv)
        
        if show_piece_boxes:
            piece_results = model2(raw_frame, conf=0.2, verbose=False, iou=0.2)
            display_frame = piece_results[0].plot(img=display_frame)

    cv2.imshow("Kamerabilde", display_frame)
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()