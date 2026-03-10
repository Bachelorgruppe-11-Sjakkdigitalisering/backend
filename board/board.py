import cv2
import numpy as np


def sort_points(pts):
    # Sorterer hjørner manuelt: [Topp-Venstre, Topp-Høyre, Bunn-Høyre, Bunn-Venstre]
    pts = np.array(pts, dtype="float32")
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def draw_grid(frame, M_inv):
    # Tegner rutenettet ved å transformere punkter fra 800x800-koordinater
    # tilbake til kamerabildet ved hjelp av M_inv
    for i in range(9):
        # Vertikale linjer
        p1 = np.array([[[i * 100, 0]]], dtype="float32")
        p2 = np.array([[[i * 100, 800]]], dtype="float32")
        t1 = cv2.perspectiveTransform(p1, M_inv)[0][0]
        t2 = cv2.perspectiveTransform(p2, M_inv)[0][0]
        cv2.line(frame, tuple(t1.astype(int)), tuple(t2.astype(int)), (0, 255, 0), 2)

        # Horisontale linjer
        p3 = np.array([[[0, i * 100]]], dtype="float32")
        p4 = np.array([[[800, i * 100]]], dtype="float32")
        t3 = cv2.perspectiveTransform(p3, M_inv)[0][0]
        t4 = cv2.perspectiveTransform(p4, M_inv)[0][0]
        cv2.line(frame, tuple(t3.astype(int)), tuple(t4.astype(int)), (0, 255, 0), 2)

        files = "abcdefgh"
        ranks = "87654321"
    
    for row in range(8):
        for col in range(8):
            # Finn sentrum av ruten i 800x800-systemet (50, 150, 250...)
            cx, cy = col * 100 + 50, row * 100 + 50
            
            # Transformer punktet tilbake til kamera-perspektivet
            p = np.array([[[cx, cy]]], dtype="float32")
            tp = cv2.perspectiveTransform(p, M_inv)[0][0]
            
            # Skriv teksten på bildet
            text = f"{files[col]}{ranks[row]}"
            cv2.putText(frame, text, tuple(tp.astype(int)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)