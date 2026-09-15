# BloodLY

BloodLY is a real-time blood tube monitoring system that uses a browser camera, computer vision, and optional AI OCR to detect tubes, classify them, and display live counts on a web dashboard and an ESP32 OLED screen.

---

## What the system does

BloodLY processes live camera frames and:

- Detects tube-like objects in the frame
- Classifies each object using a priority pipeline:
  1. **Barcode** (most reliable)
  2. **Cap color classifier** (HSV-based)
  3. **Gemini OCR fallback** (optional, reads printed label text only)
- Separates **recognized blood tubes** from **unrecognized objects**
- Maintains a live tally by category (A+, B+, AB+, O+ by current config)
- Exposes compact JSON for an ESP32 OLED display

---

## How to use BloodLY

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

### 2) Configure behavior

Edit:

- `/home/runner/work/BloodLY/BloodLY/config.py`

Key settings:

- Camera and frame settings
- Tube contour thresholds
- Cap color HSV ranges
- Barcode/Gemini toggles
- Flask host/port and dashboard refresh timing

### 3) Start the app

```bash
python app.py
```

Open:

- `http://localhost:5000/`

Grant browser camera access when prompted.

### 4) Calibrate for your environment (recommended)

```bash
python calibrate.py
```

Use the threshold trackbar and click caps to sample HSV values, then update `config.py`.

---

## Model wiring and decision flow

The runtime pipeline is wired as follows:

1. Frontend captures a frame from browser camera and sends it to `POST /api/process_frame`.
2. `vision/tube_counter.py` finds candidate tube bounding boxes using contour and morphology filters.
3. For each crop, `app.py` runs `classify_tube()` in this order:
   - `vision/barcode_reader.py` (`pyzbar`)
   - `vision/color_classifier.py` (HSV mask matching from configured cap ranges)
   - `vision/gemini_ocr.py` (**only if enabled**) with `google-genai` model (`GEMINI_MODEL`)
4. State is updated with:
   - `total_tubes` (recognized)
   - `unrecognized_count`
   - `by_category`
   - Per-tube source and confidence
5. Dashboard renders overlays and counters from API responses.
6. ESP32 polls `GET /api/display_summary` for compact counts and renders them on OLED.

### AI model behavior (Gemini fallback)

- Used only when barcode and cap color both fail
- Prompt explicitly forbids inferring blood type from liquid appearance
- Returns strict JSON (`blood_type`, `id_text`, `confidence`)
- In-memory cache avoids repeated calls for identical crops

---

## API endpoints

- `GET /` → dashboard UI
- `POST /api/process_frame` → detect/classify tubes from base64 image
- `GET /api/display_summary` → compact totals for ESP32
- `POST /api/set_threshold` → update detection threshold at runtime
- `POST /api/sample_hsv` → sample HSV at clicked pixel

---

## ESP32 OLED integration

Client sketch:

- `/home/runner/work/BloodLY/BloodLY/esp32_oled/esp32_oled.ino`

### Wiring (I2C)

| OLED | ESP32 Dev Module |
| --- | --- |
| VCC | 3V3 |
| GND | GND |
| SDA | GPIO 21 |
| SCL | GPIO 22 |

### Setup notes

- Set `WIFI_SSID`, `WIFI_PASSWORD`, and `SUMMARY_URL` in the sketch
- Install Arduino libraries: **U8g2** and **ArduinoJson**
- Ensure Flask is reachable from ESP32 (public HTTPS URL if using Codespaces forwarding)
- Display refreshes every 1.5s and redraws only on value changes to avoid blinking

---

## Repository structure

- `app.py` — Flask server, frame processing API, shared state
- `config.py` — all runtime knobs and thresholds
- `calibrate.py` — interactive threshold/HSV calibration helper
- `templates/index.html` — dashboard UI and browser camera logic
- `vision/tube_counter.py` — contour-based object detection
- `vision/color_classifier.py` — HSV cap color classification
- `vision/barcode_reader.py` — barcode decode path
- `vision/gemini_ocr.py` — optional Gemini OCR fallback
- `esp32_oled/esp32_oled.ino` — ESP32 OLED client

---

## Why this is useful

BloodLY provides a low-cost, practical workflow for live blood tube counting and categorization in demos, lab-like setups, or prototyping environments where quick visual inventory and remote display output are valuable.

---

## Contributors

Based on repository git history:

- **Momeen Bashar** (`@Bashar071`)
- **bashar017**

