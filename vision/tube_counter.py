"""
Detects candidate tube regions in a frame using simple contour analysis.
Works well with a plain, high-contrast tray. For cluttered/variable
backgrounds, swap this for a trained YOLOv8 detector for real reliability.
"""
import cv2
from config import THRESHOLD_VALUE, MIN_TUBE_AREA, MAX_TUBE_AREA


def find_tubes(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, THRESHOLD_VALUE, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for c in contours:
        area = cv2.contourArea(c)
        if MIN_TUBE_AREA <= area <= MAX_TUBE_AREA:
            x, y, w, h = cv2.boundingRect(c)
            if h > w * 1.1:  # tubes are taller than wide
                boxes.append((x, y, w, h))
    return boxes