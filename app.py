"""
Main app: runs continuous camera capture + detection in a background thread,
and serves a live dashboard over Flask.
Run with: python app.py, then open http://localhost:5000
"""
import threading
import time
import cv2
from flask import Flask, jsonify, render_template

import config
from vision.tube_counter import find_tubes
from vision.barcode_reader import read_barcode
from vision.color_classifier import classify_cap_color
from vision.gemini_ocr import read_label_with_gemini

app = Flask(__name__)

state_lock = threading.Lock()
state = {
    "total_tubes": 0,
    "by_category": {},
    "tubes": [],
    "last_updated": None,
    "camera_ok": False,
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

    return "Unknown", "none", "low"


def camera_loop():
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    if not cap.isOpened():
        with state_lock:
            state["camera_ok"] = False
        print("ERROR: Could not open camera. Check CAMERA_INDEX in config.py.")
        return

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.5)
            continue

        frame_count += 1
        if frame_count % config.PROCESS_EVERY_N_FRAMES != 0:
            continue

        boxes = find_tubes(frame)
        results = []
        tally = {}

        for (x, y, w, h) in boxes:
            crop = frame[y:y + h, x:x + w]
            category, source, confidence = classify_tube(crop)
            results.append({
                "bbox": [x, y, w, h],
                "category": category,
                "source": source,
                "confidence": confidence,
            })
            tally[category] = tally.get(category, 0) + 1

        with state_lock:
            state["total_tubes"] = len(boxes)
            state["by_category"] = tally
            state["tubes"] = results
            state["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
            state["camera_ok"] = True

    cap.release()


@app.route("/")
def dashboard():
    return render_template("index.html", refresh_ms=config.DASHBOARD_REFRESH_MS)


@app.route("/api/counts")
def api_counts():
    with state_lock:
        return jsonify(state)


if __name__ == "__main__":
    t = threading.Thread(target=camera_loop, daemon=True)
    t.start()
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=False)