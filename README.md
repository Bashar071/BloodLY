# BloodLY

BloodLY is a real-time computer vision system designed to detect, identify, and count blood sample tubes from a webcam feed. It uses a multi-modal approach for classification, prioritizing barcodes, then cap color, and finally offering an optional AI-powered OCR fallback. The system includes an interactive web dashboard for monitoring and a client for displaying results on an external ESP32-powered OLED screen.

## Features

*   **Real-Time Detection:** Identifies tube-like objects in a live video stream using OpenCV.
*   **Multi-Modal Identification:**
    *   **Barcode:** Reliably identifies tubes using `pyzbar` if a barcode is visible.
    *   **Cap Color:** Classifies tubes based on pre-configured HSV color ranges for their caps.
    *   **Gemini OCR (Optional):** Uses Google's Gemini model as a fallback to read printed labels if other methods fail.
*   **Interactive Web Dashboard:** A Flask-based web UI displays the live camera feed with detection overlays, a summary of counts, and a detailed list of detected tubes.
*   **On-the-Fly Calibration:** Adjust the detection threshold and sample cap colors directly from the web dashboard to tune the system for your environment.
*   **ESP32 OLED Display Support:** An API endpoint provides a compact summary of detections, ready to be displayed on an external OLED screen connected to an ESP32.

## How It Works

The detection process follows a prioritized pipeline for each frame captured from the camera:

1.  **Tube Finding:** The system processes the video frame to find contours that match the expected shape, size, and aspect ratio of a blood tube.
2.  **Classification Cascade:** For each potential tube detected, it attempts to identify it in the following order:
    1.  **Barcode Reading:** It first tries to decode a barcode. If successful, this result is used as the definitive identifier.
    2.  **Cap Color Analysis:** If no barcode is found, it analyzes the top portion of the object. If the color matches a known blood type in `config.py`, it's classified accordingly.
    3.  **Gemini OCR Fallback:** If both barcode and color identification fail, and `ENABLE_GEMINI_FALLBACK` is `True`, the image crop is sent to the Gemini API to read the text on the label.
3.  **Aggregation:** Results are tallied, and the state is updated. Unrecognized objects are counted separately.
4.  **Display:** The updated results are sent to the web dashboard for visualization and made available to the ESP32 client.

## Setup and Usage

### 1. Prerequisites

*   Python 3.x
*   A webcam connected to your computer.
*   (Optional) A Google API key for Gemini if you intend to use the OCR fallback.

### 2. Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/bashar071/bloodly.git
    cd bloodly
    ```

2.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

### 3. Configuration

All major settings are in `config.py`. Before running, you may need to adjust these to fit your specific setup:

*   **`CAP_COLOR_RANGES`**: This is the most important setting. Define the HSV color ranges for each blood type cap you want to detect. You can find these values using the calibration tools.
*   **`THRESHOLD_VALUE`**: The initial binary threshold for object detection.
*   **`CAMERA_INDEX`**: The index of your webcam (usually `0`).
*   **`ENABLE_GEMINI_FALLBACK`**: Set to `True` to enable the OCR fallback. You must also configure your Google API key (e.g., by setting the `GOOGLE_API_KEY` environment variable).

### 4. Calibration

Accurate detection depends on proper calibration for your lighting conditions and tube types.

*   **Method 1: Using the Calibration Script (for initial setup)**
    Run the interactive command-line tool:
    ```bash
    python calibrate.py
    ```
    -   Adjust the "Thresh" trackbar until the tubes are clearly visible as white shapes on a black background in the "Threshold" window. Note the value for `THRESHOLD_VALUE`.
    -   Click on different colored caps in the "Camera" window. The HSV values will be printed to the console. Use these values to populate the `CAP_COLOR_RANGES` dictionary in `config.py`.

*   **Method 2: Using the Web Dashboard (for fine-tuning)**
    After starting the main application, you can use the controls on the dashboard to fine-tune the system in real-time:
    -   Use the "Detection threshold" slider to adjust the threshold.
    -   Click on the video feed to sample HSV colors, which are displayed on the page.

### 5. Running the Application

1.  Start the Flask server:
    ```bash
    python app.py
    ```

2.  Open your web browser and navigate to `http://127.0.0.1:5000`. You should see the dashboard with your live camera feed.

## ESP32 OLED Display

The Flask app exposes a compact summary of the latest detections, which is ideal for a small external display.

**API Endpoint:** `GET /api/display_summary`

**Example Response:**
```json
{"categories":{"A+":2,"B+":1},"total":3,"unrecognized":1,"updated":"2026-09-15 12:00:00"}
```

The ready-to-upload Arduino sketch is located at `esp32_oled/esp32_oled.ino`. It is designed for an **ESP32 Dev Module** and a 128-pixel-wide I2C SSD1306 OLED.

### Wiring

| OLED | ESP32 Dev Module |
|------|------------------|
| VCC  | 3V3              |
| GND  | GND              |
| SDA  | GPIO 21          |
| SCL  | GPIO 22          |

### Setup

1.  In the sketch (`esp32_oled.ino`), set your `WIFI_SSID`, `WIFI_PASSWORD`, and the `SUMMARY_URL` to point to the `/api/display_summary` endpoint of your running BloodLY instance.
2.  In the Arduino IDE, select **ESP32 Dev Module** as your board.
3.  Install the **U8g2** and **ArduinoJson** libraries from the Library Manager.
4.  Start the BloodLY server with `python app.py`. Ensure your ESP32 can reach the host running the server.
5.  Upload the sketch to your ESP32. The OLED will show counts for `DETECTED`, `UNKNOWN`, and each blood group. The display only redraws when a count changes to prevent flickering.

### OLED Hardware Check

-   The sketch defaults to a 128x64 SSD1306 display.
-   For a 128x32 SSD1306, set `OLED_IS_128X32` to `1`.
-   For a 128x64 SH1106, set `OLED_IS_SH1106` to `1`.
-   The default I2C address is `0x3C`. If your display uses `0x3D`, change the `OLED_ADDRESS` value.
-   Open the Serial Monitor at 115200 baud after upload. The startup log should confirm that it found a device at the correct I2C address.
-   If the OLED shows `Server unavailable`, ensure the `SUMMARY_URL` is correct and accessible from the ESP32's network. Try opening the URL in a browser first.