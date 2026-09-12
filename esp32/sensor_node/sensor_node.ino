/*
 * Smart Farming Assistant — ESP32 Sensor Node Firmware (SIH 26180)
 * 
 * Hardware Configuration:
 *   - Microcontroller: ESP32-WROOM-32
 *   - DHT22 (Temperature & Humidity): GPIO 4
 *   - Capacitive Soil Moisture Sensor: GPIO 34 (ADC1_CH6)
 *   - Rain Sensor: GPIO 35 (ADC1_CH7)
 * 
 * Calibration Values:
 *   - Soil: SOIL_DRY = 3000, SOIL_WET = 1500
 *   - Rain: RAIN_DRY = 4095, RAIN_WET = 800
 * 
 * Network & Backend:
 *   - Target URL: http://10.63.158.132:8000/api/v1/sensors/ingest
 *   - Method: HTTP POST (Content-Type: application/json)
 *   - Interval: Every 2 seconds
 *   - Non-blocking: Sensor readings continue uninterrupted even if Wi-Fi/Backend fails.
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include "DHTesp.h"


const char *WIFI_SSID = "ItBurnsWhenIP";
const char* WIFI_PASSWORD = "mainnahibtata";

const char* BACKEND_URL   = "http://10.63.158.132:8000/api/v1/sensors/ingest";
const char* SENSOR_ID     = "esp32_field_01";

#define DHT_PIN  4
#define SOIL_PIN 34
#define RAIN_PIN 35

const int SOIL_DRY = 3000;
const int SOIL_WET = 1500;

const int RAIN_DRY = 4095;
const int RAIN_WET = 800;

DHTesp dhtSensor;

void setup() {
  Serial.begin(115200);

  
  dhtSensor.setup(DHT_PIN, DHTesp::DHT22);

  analogReadResolution(12);

  Serial.println("================================");
  Serial.println("   SMART FARM SENSOR SYSTEM");
  Serial.println("================================");

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("[WiFi] Connecting to: ");
  Serial.println(WIFI_SSID);

  // Non-blocking initial connection attempt (up to 6 seconds)
  // Ensures sensor loop starts immediately even if Wi-Fi is temporarily absent
  unsigned long startAttempt = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startAttempt < 6000) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("[WiFi] Connected! IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("[WiFi] Initial connection timeout. Loop will start and retry in background.");
  }
}

void loop() {
  TempAndHumidity data = dhtSensor.getTempAndHumidity();

  int soilRaw = analogRead(SOIL_PIN);

  int soilPercent = map(
    soilRaw,
    SOIL_DRY,
    SOIL_WET,
    0,
    100
  );

  soilPercent = constrain(soilPercent, 0, 100);

  int rainRaw = analogRead(RAIN_PIN);

  int rainPercent = map(
    rainRaw,
    RAIN_DRY,
    RAIN_WET,
    0,
    100
  );

  rainPercent = constrain(rainPercent, 0, 100);


  Serial.println();
  Serial.println("========== FARM DATA ==========");

  Serial.print("Temperature : ");
  Serial.print(data.temperature, 1);
  Serial.println(" °C");

  Serial.print("Humidity    : ");
  Serial.print(data.humidity, 1);
  Serial.println(" %");

  Serial.print("Soil Raw    : ");
  Serial.println(soilRaw);

  Serial.print("Soil Moist. : ");
  Serial.print(soilPercent);
  Serial.println(" %");

  Serial.print("Rain Raw    : ");
  Serial.println(rainRaw);

  Serial.print("Rain Level  : ");
  Serial.print(rainPercent);
  Serial.println(" %");

  Serial.println("===============================");


  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WiFi] Status: Disconnected (reconnecting in background...)");
    WiFi.reconnect();
  } else {
    Serial.print("[WiFi] Status: Connected (IP: ");
    Serial.print(WiFi.localIP());
    Serial.println(")");

    // Sanitize DHT values to prevent NaN in JSON
    float tempVal = isnan(data.temperature) ? 0.0 : data.temperature;
    float humVal  = isnan(data.humidity)    ? 0.0 : data.humidity;

    // Construct telemetry JSON matching FastAPI backend Pydantic schema
    char jsonBuffer[256];
    snprintf(
      jsonBuffer,
      sizeof(jsonBuffer),
      "{\"sensor_id\":\"%s\",\"soil_moisture\":%.1f,\"temperature\":%.1f,\"humidity\":%.1f,\"rain_level\":%.1f}",
      SENSOR_ID,
      (float)soilPercent,
      tempVal,
      humVal,
      (float)rainPercent
    );

    HTTPClient http;
    // Set a strict 2000ms timeout so network delays never freeze the sensor loop
    http.setTimeout(2000);

    if (http.begin(BACKEND_URL)) {
      http.addHeader("Content-Type", "application/json");

      int httpResponseCode = http.POST((uint8_t*)jsonBuffer, strlen(jsonBuffer));

      Serial.print("[HTTP] POST Status Code: ");
      Serial.println(httpResponseCode);

      if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.print("[Backend Response]: ");
        Serial.println(response);
      } else {
        Serial.print("[HTTP] POST failed, error: ");
        Serial.println(http.errorToString(httpResponseCode).c_str());
      }

      http.end();
    } else {
      Serial.println("[HTTP] Unable to connect to backend URL");
    }
  }
  delay(2000);
}
