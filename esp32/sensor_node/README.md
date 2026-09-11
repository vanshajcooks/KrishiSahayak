# ESP32 Sensor Node — Hardware & Telemetry Guide

**Responsible Teammates**: Sneha (Hardware/IoT) & Vanshaj (Integration)  
**Hardware Platform**: ESP32-WROOM-32

---

## 1. Overview & Important Note

> [!IMPORTANT]
> **Working Code Preservation Notice**:  
> Per architecture guidelines, existing working sensor-node code is **not** replaced or modified at this milestone. Final ESP32 HTTP communication will be enabled in Milestone 2 once the backend ingestion pipeline is confirmed.

This folder serves as the central location for the ESP32 sensor controller firmware, pinout definitions, and telemetry contracts.

---

## 2. Hardware Components & Pinout Configuration

| Component | Interface Type | ESP32 GPIO Pin | Operating Voltage | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Capacitive Soil Moisture Sensor v1.2** | Analog (ADC) | `GPIO 34` (ADC1_CH6) | 3.3V | Corrosion-resistant capacitive probe |
| **DHT22 Temperature & Humidity** | Digital 1-Wire | `GPIO 4` | 3.3V / 5V | Requires 10k pull-up resistor if breakout lacks one |
| **Status LED** | Digital Output | `GPIO 2` | 3.3V | Internal blue LED indicates WiFi/transmit status |
| **Battery Voltage Monitor** | Analog Divider | `GPIO 35` (ADC1_CH7) | 3.3V | Voltage divider (2x 100k resistors) for 3.7V Li-ion |

> [!TIP]
> Use ADC1 pins (GPIO 32–39) on the ESP32 when WiFi is active. ADC2 pins are shared with the WiFi peripheral and will produce erroneous readings while WiFi is transmitting.

---

## 3. Soil Moisture Sensor Calibration Guide

Capacitive soil moisture sensors output an analog voltage inversely proportional to soil moisture (higher voltage = dry, lower voltage = submerged).

Sneha's calibration steps:
1. **Air Value (0% Moisture)**: Hold the dry sensor in the air, record the raw 12-bit ADC value (typically `~3000–3500`).
2. **Water Value (100% Moisture)**: Submerge the sensor up to the white line in a cup of water, record the ADC value (typically `~1200–1500`).
3. **Conversion Formula**:
   $$\text{Moisture (\%)} = \text{constrain}\left(\frac{\text{AirValue} - \text{RawValue}}{\text{AirValue} - \text{WaterValue}} \times 100.0, \, 0.0, \, 100.0\right)$$

---

## 4. Telemetry Contract (HTTP/JSON)

When HTTP transmission is enabled in Milestone 2, the ESP32 will send an HTTP `POST` to `/api/v1/sensors/ingest` with this JSON payload:

```json
{
  "sensor_id": "esp32_field_01",
  "soil_moisture": 45.2,
  "temperature": 29.1,
  "humidity": 63.8,
  "battery_voltage": 3.98
}
```

### Destination Hosts:
- **Development**: IP of development PC (e.g., `http://192.168.1.150:8000/api/v1/sensors/ingest`)
- **Field Deployment**: Static IP of Raspberry Pi gateway hotspot (e.g., `http://192.168.4.1:8000/api/v1/sensors/ingest`)
