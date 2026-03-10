import cv2
import numpy as np


def get_occupied_squares_on_raw_frame(frame, model, M):
    results = model(frame, conf=0.3, verbose=False)
    occupied = []
    
    if len(results[0].boxes) > 0:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        for box in boxes:
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
                occupied.append((row, col))
                
    return list(set(occupied))