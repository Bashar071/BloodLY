"""
Browser-camera version with bottle/tube validation and an ESP32 display feed.
"""
import base64
import threading
import time

import cv2
import numpy as np
from flask import Flask, jsonify, render_template, request

import config
from vision.tube_counter import find_tubes
from vision.barcode_reader import read_barcode
from vision.color_classifier import classify_cap_color
from vision.gemini_ocr import read_label_with_gemini

app = Flask(__name__)

state_lock = threading.Lock()
state = {
    "total_tubes": 0,          # valid, recognized blood tubes only
    "unrecognized_count": 0,   # objects seen but not matching any known cap
    "by_category": {},
    "tubes": [],
    "last_updated": None,
}


def classify_tube(crop):
    if config.ENABLE_BARCODE:
        barcode = read_barcode(crop)
        if barcode:
            return barcode, "barcode", "high"

    color_match = classify_cap_color(crop)
    if color_match:
        return color_match, "cap_color", "high"

    if config.ENABLE_GEMINI_FALLBACK:
        result = read_label_with_gemini(crop)
        if result.get("blood_type"):
            return result["blood_type"], "gemini_ocr", result.get("confidence", "medium")

    return "Unrecognized", "none", "low"


def decode_base64_image(data_url):
    header, encoded = data_url.split(",", 1)
    img_bytes = base64.b64decode(encoded)
    arr = np.frombuffer(img_bytes, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


@app.route("/")
def dashboard():
    return render_template("index.html", refresh_ms=config.DASHBOARD_REFRESH_MS)


@app.route("/api/process_frame", methods=["POST"])
def process_frame():
    payload = request.get_json()
    frame = decode_base64_image(payload["image"])
    if frame is None:
        return jsonify({"error": "could not decode image"}), 400

    boxes = find_tubes(frame)
    results = []
    tally = {}
    unrecognized = 0

    for (x, y, w, h) in boxes:
        crop = frame[y:y + h, x:x + w]
        category, source, confidence = classify_tube(crop)
        results.append({"bbox": [int(x), int(y), int(w), int(h)],
                         "category": category, "source": source, "confidence": confidence})

        if category == "Unrecognized":
            unrecognized += 1
            if not config.EXCLUDE_UNKNOWN_FROM_COUNT:
                tally[category] = tally.get(category, 0) + 1
        else:
            tally[category] = tally.get(category, 0) + 1

    valid_total = sum(tally.values())

    with state_lock:
        state.update({
            "total_tubes": valid_total,
            "unrecognized_count": unrecognized,
            "by_category": tally,
            "tubes": results,
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        })

    return jsonify(state)


@app.route("/api/display_summary")
def display_summary():
    """Compact JSON for the ESP32 OLED display -- small payload, easy to parse."""
    with state_lock:
        return jsonify({
            "total": state["total_tubes"],
            "unrecognized": state["unrecognized_count"],
            "categories": state["by_category"],
            "updated": state["last_updated"],
        })


@app.route("/api/set_threshold", methods=["POST"])
def set_threshold():
    config.THRESHOLD_VALUE = int(request.get_json()["value"])
    return jsonify({"ok": True, "threshold": config.THRESHOLD_VALUE})


@app.route("/api/sample_hsv", methods=["POST"])
def sample_hsv():
    payload = request.get_json()
    frame = decode_base64_image(payload["image"])
    x, y = int(payload["x"]), int(payload["y"])
    if frame is None or not (0 <= y < frame.shape[0] and 0 <= x < frame.shape[1]):
        return jsonify({"error": "invalid image or coordinates"}), 400
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[y, x]
    return jsonify({"h": int(h), "s": int(s), "v": int(v)})


if __name__ == "__main__":
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=False)