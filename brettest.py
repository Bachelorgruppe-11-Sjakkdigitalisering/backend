import cv2
import numpy as np
from ultralytics import YOLO
from collections import deque

# 1. Konfigurasjon
MODEL_PATH = 'brett.pt'
SMOOTHING_FRAMES = 10  # Antall frames vi snitter hjørnene over for stabilitet

# Last inn modellen
model = YOLO(MODEL_PATH)

def sort_points(pts):
    """Sorterer punkter: [Topp-Venstre, Topp-Høyre, Bunn-Høyre, Bunn-Venstre]"""
    pts = np.array(pts, dtype="float32")
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def main():
    cap = cv2.VideoCapture(0)
    
    # Buffer for å lagre hjørneposisjoner over tid
    corner_history = deque(maxlen=SMOOTHING_FRAMES)

    print("Starter sjakk-deteksjon. Trykk 'q' for å avslutte.")

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # Kjør modellen på gjeldende bilde
        results = model(frame, conf=0.1, iou=0.3, verbose=False)
        boxes_objs = results[0].boxes

        # 1. Finn hjørnene hvis modellen ser minst 4
        if len(boxes_objs) >= 4:
            all_boxes = boxes_objs.xyxy.cpu().numpy()
            all_confs = boxes_objs.conf.cpu().numpy()

            # Velg de 4 sikreste boksene
            top4_indices = np.argsort(all_confs)[-4:]
            best_boxes = all_boxes[top4_indices]
            
            current_corners = []
            for box in best_boxes:
                current_corners.append([(box[0] + box[2]) / 2, (box[1] + box[3]) / 2])
            
            sorted_curr = sort_points(current_corners)
            corner_history.append(sorted_curr)
            
        # 2. Tegn rutenettet hvis vi har data i historikken
        if len(corner_history) > 0:
            avg_corners = np.mean(corner_history, axis=0).astype("float32")
            size = 800
            dst = np.float32([[0, 0], [size, 0], [size, size], [0, size]])
          
            try:   
                M_inv = cv2.getPerspectiveTransform(dst, avg_corners)

                # --- TEGN RUTENETTET ---
                for i in range(9):
                    # Vertikale linjer
                    pts_v = np.array([[[i*100, 0]], [[i*100, 800]]], dtype="float32")
                    trans_v = cv2.perspectiveTransform(pts_v, M_inv)
                    cv2.line(frame, tuple(trans_v[0][0].astype(int)), tuple(trans_v[1][0].astype(int)), (0, 255, 0), 2)

                    # Horisontale linjer
                    pts_h = np.array([[[0, i*100]], [[800, i*100]]], dtype="float32")
                    trans_h = cv2.perspectiveTransform(pts_h, M_inv)
                    cv2.line(frame, tuple(trans_h[0][0].astype(int)), tuple(trans_h[1][0].astype(int)), (0, 255, 0), 2)

                # --- TEGN KOORDINATER ---
                files = "abcdefgh"
                ranks = "87654321"
                for row in range(8):
                    for col in range(8):
                        cx, cy = col * 100 + 50, row * 100 + 50
                        p = np.array([[[cx, cy]]], dtype="float32")
                        tp = cv2.perspectiveTransform(p, M_inv)[0][0]
                        cv2.putText(frame, f"{files[col]}{ranks[row]}", tuple(tp.astype(int)), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            except:
                pass        

        # Vis resultatet
        cv2.imshow("Sjakkbrett-rutenett", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()