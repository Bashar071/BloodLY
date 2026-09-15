"""
Classifies a tube's cap color against configured HSV ranges.
"""
import cv2
import numpy as np
from config import CAP_COLOR_RANGES, MIN_COLOR_MATCH_RATIO, CAP_REGION_FRACTION


def classify_cap_color(tube_crop):
    h, w = tube_crop.shape[:2]
    if h == 0 or w == 0:
        return None

    cap_h = max(1, int(h * CAP_REGION_FRACTION))
    cap_region = tube_crop[0:cap_h, 0:w]

    hsv = cv2.cvtColor(cap_region, cv2.COLOR_BGR2HSV)
    total_pixels = cap_region.shape[0] * cap_region.shape[1]
    if total_pixels == 0:
        return None

    best_match, best_ratio = None, 0.0
    for category, bounds in CAP_COLOR_RANGES.items():
        lower = np.array(bounds["lower"])
        upper = np.array(bounds["upper"])
        mask = cv2.inRange(hsv, lower, upper)
        match_ratio = cv2.countNonZero(mask) / total_pixels
        if match_ratio > best_ratio:
            best_ratio, best_match = match_ratio, category

    if best_ratio >= MIN_COLOR_MATCH_RATIO:
        return best_match
    return None