#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <U8g2lib.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <Wire.h>

const char *WIFI_SSID = "10S";
const char *WIFI_PASSWORD = "11111111";
// Codespaces exposes Flask through this public HTTPS port-forward URL.
const char *SUMMARY_URL = "https://sturdy-succotash-4jqwqjrj7rj92qgv-5000.app.github.dev/api/display_summary";

// Use the constructor that matches the actual controller and panel size.
// The attached display is a 128x64 panel: use the full-height constructor.
#define OLED_IS_SH1106 0
#define OLED_IS_128X32 0
#define OLED_SDA 21
#define OLED_SCL 22
#define OLED_ADDRESS 0x3C

#if OLED_IS_SH1106
U8G2_SH1106_128X64_NONAME_F_HW_I2C display(U8G2_R0, U8X8_PIN_NONE);
#elif OLED_IS_128X32
U8G2_SSD1306_128X32_UNIVISION_F_HW_I2C display(U8G2_R0, U8X8_PIN_NONE);
#else
U8G2_SSD1306_128X64_NONAME_F_HW_I2C display(U8G2_R0, U8X8_PIN_NONE);
#endif
unsigned long lastPoll = 0;
const unsigned long POLL_INTERVAL_MS = 1500;
bool hasSummary = false;

struct SummaryState {
  int total;
  int unrecognized;
  int aPlus;
  int bPlus;
  int abPlus;
  int oPlus;
};

SummaryState currentSummary = {0, 0, 0, 0, 0, 0};

void showMessage(const char *line1, const char *line2 = "") {
  display.clearBuffer();
  display.setFont(u8g2_font_6x10_tf);
  display.drawStr(0, 10, line1);
  display.drawStr(0, 22, line2);
  display.sendBuffer();
}

void scanI2C() {
  Serial.println("I2C scan:");
  for (uint8_t address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    if (Wire.endTransmission() == 0) {
      Serial.printf("Found OLED/device at 0x%02X\n", address);
    }
  }
}

void connectWifi() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  showMessage("Connecting WiFi...", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long started = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - started < 15000) {
    delay(250);
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());
    Serial.print("Flask URL: ");
    Serial.println(SUMMARY_URL);
  } else {
    Serial.println("WiFi connection failed");
  }
}

bool summaryChanged(const SummaryState &next) {
  return !hasSummary ||
         next.total != currentSummary.total ||
         next.unrecognized != currentSummary.unrecognized ||
         next.aPlus != currentSummary.aPlus ||
         next.bPlus != currentSummary.bPlus ||
         next.abPlus != currentSummary.abPlus ||
         next.oPlus != currentSummary.oPlus;
}

void drawSummary(const SummaryState &summary) {
  if (!summaryChanged(summary)) {
    return;
  }

  currentSummary = summary;
  hasSummary = true;

  display.clearBuffer();
  display.setFont(u8g2_font_6x10_tf);
#if OLED_IS_128X32
  char line[24];
  snprintf(line, sizeof(line), "D:%d U:%d", summary.total, summary.unrecognized);
  display.drawStr(0, 9, line);
  snprintf(line, sizeof(line), "A:%d B:%d", summary.aPlus, summary.bPlus);
  display.drawStr(0, 19, line);
  snprintf(line, sizeof(line), "AB:%d O:%d", summary.abPlus, summary.oPlus);
  display.drawStr(0, 29, line);
#else
  char line[32];
  display.setFont(u8g2_font_7x13B_tf);
  snprintf(line, sizeof(line), "DETECTED: %d", summary.total);
  display.drawStr(4, 13, line);
  snprintf(line, sizeof(line), "UNKNOWN: %d", summary.unrecognized);
  display.drawStr(4, 27, line);
  snprintf(line, sizeof(line), "A+:%d  B+:%d", summary.aPlus, summary.bPlus);
  display.drawStr(4, 43, line);
  snprintf(line, sizeof(line), "AB+:%d O+:%d", summary.abPlus, summary.oPlus);
  display.drawStr(4, 59, line);
#endif
  display.sendBuffer();
}

void fetchSummary() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWifi();
    if (WiFi.status() != WL_CONNECTED) {
      showMessage("WiFi unavailable", "Retrying...");
      return;
    }
  }

  WiFiClientSecure client;
  // The forwarded URL uses a public certificate. This avoids certificate
  // bundle issues on the ESP32; use a CA certificate for production devices.
  client.setInsecure();
  HTTPClient http;
  http.setTimeout(3000);
  if (!http.begin(client, SUMMARY_URL)) {
    showMessage("HTTP setup failed");
    return;
  }

  int status = http.GET();
  if (status == HTTP_CODE_OK) {
    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, http.getString());
    if (error) {
      showMessage("Invalid server data");
    } else {
      JsonObject categories = doc["categories"];
      SummaryState next = {
        doc["total"] | 0,
        doc["unrecognized"] | 0,
        categories["A+"] | 0,
        categories["B+"] | 0,
        categories["AB+"] | 0,
        categories["O+"] | 0,
      };
      drawSummary(next);
    }
  } else {
    Serial.print("HTTP request failed, code: ");
    Serial.println(status);
    showMessage("Server unavailable", String(status).c_str());
  }
  http.end();
}

void setup() {
  Serial.begin(115200);
  Wire.begin(OLED_SDA, OLED_SCL);
  Wire.setClock(100000);
  delay(100);
  scanI2C();

  display.setI2CAddress(OLED_ADDRESS << 1);
  display.begin();
  display.clearBuffer();
  display.sendBuffer();
  showMessage("Starting BloodLY...");
  connectWifi();
  fetchSummary();
}

void loop() {
  if (millis() - lastPoll >= POLL_INTERVAL_MS) {
    lastPoll = millis();
    fetchSummary();
  }
}
