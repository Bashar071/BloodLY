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
MAX_TUBE_AREA = 150000

# --- Cap color categories ---
CAP_COLOR_RANGES = {
    "A+":  [{"lower": (0, 90, 60), "upper": (8, 255, 255)},
            {"lower": (170, 90, 60), "upper": (180, 255, 255)}],  # red
    "B+":  {"lower": (95, 90, 60), "upper": (130, 255, 255)},     # blue
    "AB+": {"lower": (10, 90, 60), "upper": (24, 255, 255)},      # yellow/orange
    "O+":  {"lower": (25, 70, 60), "upper": (85, 255, 255)},      # green, including lime shades
}
MIN_COLOR_MATCH_RATIO = 0.10   # a cap can occupy only a small part of the bottle crop


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

# --- Bottle vs. tube validation ---
# A detected object only counts as a "blood tube" if its cap color matches
# one of CAP_COLOR_RANGES above (or has a valid barcode). Anything else is
# shown separately as "unrecognized" and excluded from the blood tally.
# This is what lets plain water bottles (used as tube stand-ins in your
# demo) be filtered out automatically based on cap color alone.
EXCLUDE_UNKNOWN_FROM_COUNT = True

# Loosen the shape filter slightly since standard water bottles are a bit
# wider relative to height than real lab tubes.
BOTTLE_MIN_ASPECT_RATIO = 1.0   # height must be at least this many times the width

MIN_SOLIDITY = 0.65  # 0-1. Keep irregular bottle silhouettes so they can be classified