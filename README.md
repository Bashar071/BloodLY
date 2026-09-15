# BloodLY

## ESP32 OLED display

The Flask app exposes the latest detection summary at:

`GET /api/display_summary`

Example response:

```json
{"categories":{"A+":2,"B+":1},"total":3,"unrecognized":1,"updated":"2026-09-15 12:00:00"}
```

The ready-to-upload client is in [esp32_oled/esp32_oled.ino](esp32_oled/esp32_oled.ino). It is intended for an ESP32 Dev Module and a 128-pixel-wide I2C SSD1306 OLED.

### Wiring

| OLED | ESP32 Dev Module |
| --- | --- |
| VCC | 3V3 |
| GND | GND |
| SDA | GPIO 21 |
| SCL | GPIO 22 |

### Setup

1. In the sketch, set `WIFI_SSID`, `WIFI_PASSWORD`, and `SUMMARY_URL`. For this Codespace, use the public HTTPS forwarded URL: `https://sturdy-succotash-4jqwqjrj7rj92qgv-5000.app.github.dev/api/display_summary`. The private `10.0.11.191` address is reachable inside the Codespace but not from the ESP32.
2. In Arduino IDE, select **ESP32 Dev Module** and install **U8g2** and **ArduinoJson**. The sketch no longer uses Adafruit SSD1306.
3. Start BloodLY with `python app.py` and keep the Codespace port 5000 forwarded as **public**. The ESP32 uses HTTPS through that forwarding URL.
4. Upload the sketch. The OLED shows `DETECTED`, `UNRECOGNIZED`, and all four blood-group counts. It polls every 1.5 seconds but redraws only when a count changes, preventing blinking.

### OLED hardware check

- A 128x64 module uses `#define SCREEN_HEIGHT 64`.
- The sketch defaults to the attached 128x64 SSD1306: `OLED_IS_128X32 0` and `OLED_IS_SH1106 0`.
- For a short 128x32 SSD1306, set `OLED_IS_128X32` to `1`.
- For a 128x64 SH1106, set `OLED_IS_SH1106` to `1` and `OLED_IS_128X32` to `0`.
- The usual I2C address is `0x3C`; change `OLED_ADDRESS` to `0x3D` if the Serial Monitor reports that address instead.
- Open Serial Monitor at 115200 baud after upload. The startup log must say `Found OLED/device at 0x3C` or `0x3D`.
- If no address is found, check VCC, GND, SDA, and SCL. Dotted pixels across the entire panel usually indicate incorrect height, address, wiring, or a display that is not SSD1306.

If the OLED stays on `Server unavailable`, open the exact HTTPS `SUMMARY_URL` in a browser. It should return JSON. The ESP32 sketch uses `WiFiClientSecure` for this URL.
"# BloodLY" 
"# BloodLY" 
