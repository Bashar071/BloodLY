"""
Central configuration for the Blood Tube Detection System.
Tune these values to match your camera, lighting, and tube/cap colors.
Use calibrate.py to help find good values interactively.
"""

# --- Camera ---
CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
PROCESS_EVERY_N_FRAMES = 5

# --- Tube detection (contour-based) ---
THRESHOLD_VALUE = 60
MIN_TUBE_AREA = 800
MAX_TUBE_AREA = 50000
CAP_REGION_FRACTION = 0.25

# --- Cap color categories ---
CAP_COLOR_RANGES = {
    "Type A (Red Cap)":     {"lower": (0, 120, 70),   "upper": (10, 255, 255)},
    "Type B (Blue Cap)":    {"lower": (100, 120, 70), "upper": (130, 255, 255)},
    "Type AB (Yellow Cap)": {"lower": (20, 120, 70),  "upper": (35, 255, 255)},
    "Type O (Green Cap)":   {"lower": (45, 120, 70),  "upper": (75, 255, 255)},
}
MIN_COLOR_MATCH_RATIO = 0.35

# --- Barcode ---
ENABLE_BARCODE = True

# --- Gemini OCR fallback (optional) ---
ENABLE_GEMINI_FALLBACK = False
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_CACHE_TTL_SECONDS = 300

# --- Dashboard ---
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
DASHBOARD_REFRESH_MS = 1500