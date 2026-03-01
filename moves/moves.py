import cv2
import numpy as np

# Startposisjon i sjakk (Store = hvit, små = svart, . = tom rute)
initial_board = [
    ["r", "n", "b", "q", "k", "b", "n", "r"],
    ["p", "p", "p", "p", "p", "p", "p", "p"],
    ["."] * 8, ["."] * 8, ["."] * 8, ["."] * 8,
    ["P", "P", "P", "P", "P", "P", "P", "P"],
    ["R", "N", "B", "Q", "K", "B", "N", "R"]
]

files = "abcdefgh"
ranks = "87654321"

def detect_move(ref_img, current_img, board_matrix):
    changes = []
    threshold = 0.15 # Hvor mye endring som skal til (følsomhet)
    
    for r in range(8):
        for c in range(8):
            # Finn ruten i det "warped" bildet (hver rute er 100x100)
            x1, y1 = c * 100, r * 100
            x2, y2 = x1 + 100, y1 + 100
            
            # Klipp ut ruten med litt marg for å unngå kantstøy
            ref_sq = ref_img[y1+15:y2-15, x1+15:x2-15]
            curr_sq = current_img[y1+15:y2-15, x1+15:x2-15]
            
            # Sammenlign forskjellen i lysstyrke
            diff = np.median(cv2.absdiff(ref_sq, curr_sq))
            brightness = max(np.mean(ref_sq), 1)
            score = diff / brightness
            
            if score > threshold:
                changes.append((score, files[c] + ranks[r]))

    # Sorter endringene slik at de største kommer først
    changes.sort(key=lambda x: x[0], reverse=True)

    if len(changes) >= 2:
        square1 = changes[0][1]
        square2 = changes[1][1]
        
        # Sjekk hvilken rute som hadde brikken (fra-rute)
        c1 = files.find(square1[0])
        r1 = 8 - int(square1[1])
        
        if board_matrix[r1][c1] != ".":
            return square1, square2
        else:
            return square2, square1
    return None