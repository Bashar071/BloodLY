import cv2
import numpy as np
import config


def find_tubes(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)  # stronger blur suppresses texture noise
    # Check both polarities. A single inverse threshold only finds dark bottles
    # and loses clear or brightly colored bottles before classification starts.
    masks = []
    for threshold_type in (cv2.THRESH_BINARY_INV, cv2.THRESH_BINARY):
        _, mask = cv2.threshold(blurred, config.THRESHOLD_VALUE, 255, threshold_type)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        masks.append(mask)

    boxes = []
    for mask in masks:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            area = cv2.contourArea(c)
            if not (config.MIN_TUBE_AREA <= area <= config.MAX_TUBE_AREA):
                continue

            x, y, w, h = cv2.boundingRect(c)
            if h <= w * config.BOTTLE_MIN_ASPECT_RATIO:
                continue

            hull_area = cv2.contourArea(cv2.convexHull(c))
            if hull_area == 0 or (area / hull_area) < config.MIN_SOLIDITY:
                continue

            candidate = (x, y, w, h)
            if not any(_boxes_overlap(candidate, existing) for existing in boxes):
                boxes.append(candidate)

    # Grayscale thresholding loses brightly colored bottles. Add candidates
    # from the configured color masks so classification can see the bottle.
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    color_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    for bounds in config.CAP_COLOR_RANGES.values():
        ranges = bounds if isinstance(bounds, list) else [bounds]
        color_mask = None
        for color_range in ranges:
            lower = np.array(color_range["lower"], dtype=np.uint8)
            upper = np.array(color_range["upper"], dtype=np.uint8)
            current = cv2.inRange(hsv, lower, upper)
            color_mask = current if color_mask is None else cv2.bitwise_or(color_mask, current)

        color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, color_kernel, iterations=3)
        contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if not (config.MIN_TUBE_AREA <= area <= config.MAX_TUBE_AREA * 2):
                continue

            x, y, w, h = cv2.boundingRect(contour)
            if h < w * 0.55:
                continue
            hull_area = cv2.contourArea(cv2.convexHull(contour))
            if hull_area == 0 or area / hull_area < 0.45:
                continue

            candidate = (x, y, w, h)
            if not any(_boxes_overlap(candidate, existing) for existing in boxes):
                boxes.append(candidate)
    return boxes


def _boxes_overlap(first, second):
    """Return true when two detections describe substantially the same object."""
    ax, ay, aw, ah = first
    bx, by, bw, bh = second
    left, top = max(ax, bx), max(ay, by)
    right, bottom = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    intersection = max(0, right - left) * max(0, bottom - top)
    smaller_area = min(aw * ah, bw * bh)
    return smaller_area > 0 and intersection / smaller_area >= 0.5