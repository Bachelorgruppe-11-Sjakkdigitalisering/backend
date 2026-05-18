import cv2
import numpy as np


def sort_points(pts):
    """Manually sorts four corner points into order.
    [top-left, top-right, bottom-right, bottom-left]"""
    # Sorterer hjørner manuelt: [Topp-Venstre, Topp-Høyre, Bunn-Høyre, Bunn-Venstre]
    pts = np.array(pts, dtype="float32")
    rect = np.zeros((4, 2), dtype="float32")

    # assumes the top-left point has the smallest sum.
    # assumes the bottom-right point has the largest sum.
    s = pts.sum(axis=1)
    rect[1] = pts[np.argmin(s)] # h1
    rect[3] = pts[np.argmax(s)] # a8

    # assumes the top-right has the sammlest diff.
    # assumes the bottom-left has the largest diff.
    diff = np.diff(pts, axis=1)
    rect[2] = pts[np.argmin(diff)] # h8
    rect[0] = pts[np.argmax(diff)] # a1
    return rect

def extract_corners(results):
    """filters the top 4 most confident corners from the yolo model."""

    if len(results[0].boxes) >= 4:
        all_boxes = results[0].boxes.xyxy.cpu().numpy()
        confs = results[0].boxes.conf.cpu().numpy()

        # get indicies of the 4 most confident detections.
        best_indices = np.argsort(confs)[-4:]
        
        pts = []
        for i in best_indices:
            box = all_boxes[i]
            # find the center of the corner bounding box.

            pts.append([(box[0] + box[2]) / 2, (box[1] + box[3]) / 2])
        
        return sort_points(pts)
    return None

def lock_perspective(history, white_side="right"):
    """calculates the transformation matrix to flatten the board.
    calculates the inverse matrix to prooject digital data back onto the video."""
    if len(history) > 0:
        # use the average of recent corner detection to reduce flickering.
        avg_corners = np.mean(history, axis=0).astype("float32")

        # define the target 800x800 flat swuare coordinates.
        # We adjust the target points based on which side of the board white is on.
        if white_side == "left":
            # Rotate image 180 degrees.
            target_pts = np.float32([[800,800], [0,800], [0,0], [800,0]])
        else:
            # Standard orientation.
            target_pts = np.float32([[0,0], [800,0], [800,800], [0,800]])

        # M: Camera View to flat 800x800 board.    
        M = cv2.getPerspectiveTransform(avg_corners, target_pts)
        # M_Inv: flat 800x800 board to camera view (used for drawing the grid).
        M_inv = cv2.getPerspectiveTransform(target_pts, avg_corners)
        return M, M_inv
    return None, None

def draw_grid(frame, M_inv):
    """draws the grid and square labels back onto the video feed, by using M_inv."""
    for i in range(9):
        # Vertical lines
        p1 = np.array([[[i * 100, 0]]], dtype="float32")
        p2 = np.array([[[i * 100, 800]]], dtype="float32")
        t1 = cv2.perspectiveTransform(p1, M_inv)[0][0]
        t2 = cv2.perspectiveTransform(p2, M_inv)[0][0]
        cv2.line(frame, tuple(t1.astype(int)), tuple(t2.astype(int)), (0, 255, 0), 2)

        # Horizontal lines
        p3 = np.array([[[0, i * 100]]], dtype="float32")
        p4 = np.array([[[800, i * 100]]], dtype="float32")
        t3 = cv2.perspectiveTransform(p3, M_inv)[0][0]
        t4 = cv2.perspectiveTransform(p4, M_inv)[0][0]
        cv2.line(frame, tuple(t3.astype(int)), tuple(t4.astype(int)), (0, 255, 0), 2)

        # labels for each square (for visual debugging and testing with admin panel).
        files = "abcdefgh"
        ranks = "87654321"
    
    for row in range(8):
        for col in range(8):
            # find the center of each swuare in the 800x800 system.
            cx, cy = col * 100 + 50, row * 100 + 50
            
            # project that center point back tro the camera view.
            p = np.array([[[cx, cy]]], dtype="float32")
            tp = cv2.perspectiveTransform(p, M_inv)[0][0]
            
            # overlay the square coordinate text.
            text = f"{files[col]}{ranks[row]}"
            cv2.putText(frame, text, tuple(tp.astype(int)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)