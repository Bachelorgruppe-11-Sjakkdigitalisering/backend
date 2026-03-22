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

def get_square_coords (col, row):
    return col * 100, row * 100, (col + 1) * 100, (row + 1) * 100

def main():
    cap = cv2.VideoCapture(0)
    
    # Buffer for å lagre hjørneposisjoner over tid
    corner_history = deque(maxlen=SMOOTHING_FRAMES)

    reference_board = None  # Lagrer fargene på brettet før trekk
    files = "abcdefgh"
    ranks = "87654321"

    print("KONTROLLER:")
    print("'s' - Lagre nåværende brett (bruk før du starter eller etter et trekk)")
    print("'l' - Finn ut hvilket trekk som er gjort")
    print("'q' - Avslutt")

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
                M = cv2.getPerspectiveTransform(avg_corners, dst)

                warped = cv2.warpPerspective(frame, M, (size, size))
                warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2HSV)
                warped_gray_v = warped_gray[:,:,2]
                key = cv2.waitKey(1) & 0xFF

                if key == ord('s'):
                    reference_board = warped_gray[:,:,2].copy()
                    print("Brett-referanse lagret!")

                if key == ord('l') and reference_board is not None:
                    # Finn differanse mellom nåværende brett og referanse
                    current_v = warped_gray[:,:,2]
                    diff = cv2.absdiff(reference_board, current_v)
                    errors = []

                    terskel = 0.05

                    for row in range(8):
                        for col in range(8):
                            x1, y1, x2, y2 = get_square_coords(col, row)
                            margin = 5
                            # Hent ut ruten fra referansen og nåværende bilde (V-kanalen)
                            ref_sq = reference_board[y1+margin:y2-margin, x1+margin:x2-margin]
                            curr_sq = current_v[y1+margin:y2-margin, x1+margin:x2-margin]
                            # Beregn gjennomsnittlig lysstyrke for ruten i referansen
                            ref_brightness = np.mean(ref_sq)
                            if ref_brightness < 1: ref_brightness = 1 # Unngå divisjon med null
                            # Beregn absolutt differanse
                            abs_diff = np.median(cv2.absdiff(ref_sq, curr_sq))
                            # NORMALISERING: 
                            # Vi dividerer differansen på referanse-lysstyrken.
                            # En endring på 20 på en svart rute (verdi 50) gir 20/50 = 0.4
                            # En endring på 20 på en hvit rute (verdi 200) gir 20/200 = 0.1
                            relative_diff = abs_diff / ref_brightness
                            # Juster terskelen (0.1 - 0.3 er ofte bra her)
                            if relative_diff > terskel: 
                                errors.append((relative_diff, f"{files[col]}{ranks[row]}"))
                            

                    # Sorter ruter etter hvor mye de har endret seg
                    errors.sort(key=lambda x: x[0], reverse=True)
                    
                    # De to rutene med størst endring er sannsynligvis fra/til
                    if len(errors) >= 2:
                        rute1 = errors[0][1]
                        rute2 = errors[1][1]
                        # Hvis rute 1 og rute 2 er naboer (f.eks d1 og d2), 
                        # se om det finnes en rute lenger unna som også har endret seg.
                        dist = abs(ord(rute1[0]) - ord(rute2[0])) + abs(int(rute1[1]) - int(rute2[1]))
                        if dist < 2 and len(errors) > 2:
                            # Hvis de to beste er naboer, er rute 2 sannsynligvis støy (skygge).
                            # Vi velger heller den neste på lista som er lenger unna.
                            rute1 = errors[0][1]
                            rute2 = errors[2][1] # Hopp over naboen
                        else:
                            rute1 = errors[0][1]
                            rute2 = errors[1][1]

                        print(f"MULIG TREKK DETEKTERT: {rute1} <-> {rute2}")
                    elif len(errors) == 1:
                        print(f"Kun én rute endret seg ({errors[0][1]}). Prøv å senke terskel verdien.")
                    else:
                        print("Ingen betydelige endringer detektert. Sjekk belysning eller senk terskel verdien.")

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