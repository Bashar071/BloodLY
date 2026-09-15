"""
Classifies a tube/bottle's color against configured HSV ranges to determine
blood group. Supports categories with multiple HSV ranges (needed for red,
which wraps around both ends of the hue scale).
"""
import cv2
import numpy as np
from config import CAP_COLOR_RANGES, MIN_COLOR_MATCH_RATIO, CAP_REGION_FRACTION


def _ranges_for(bounds):
    """Normalize a category's config entry into a list of (lower, upper) pairs."""
    if isinstance(bounds, list):
        return [(np.array(b["lower"]), np.array(b["upper"])) for b in bounds]
    return [(np.array(bounds["lower"]), np.array(bounds["upper"]))]


def classify_cap_color(tube_crop):
    h, w = tube_crop.shape[:2]
    if h == 0 or w == 0:
        return None

    best_match, best_ratio = None, 0.0
    region_h = max(1, int(h * CAP_REGION_FRACTION))
    regions = (tube_crop[0:region_h, 0:w], tube_crop)
    for region in regions:
        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
        total_pixels = region.shape[0] * region.shape[1]
        if total_pixels == 0:
            continue

        for category, bounds in CAP_COLOR_RANGES.items():
            combined_mask = None
            for lower, upper in _ranges_for(bounds):
                mask = cv2.inRange(hsv, lower, upper)
                combined_mask = mask if combined_mask is None else cv2.bitwise_or(combined_mask, mask)

            match_ratio = cv2.countNonZero(combined_mask) / total_pixels
            if match_ratio > best_ratio:
                best_ratio, best_match = match_ratio, category

    if best_ratio >= MIN_COLOR_MATCH_RATIO:
        return best_match
    return None