/*
  Hybrid Pothole Detection System
  Arduino Nano 33 IoT + ADXL345 Accelerometer
  ------------------------------------------------
  Function:
  - Reads 3-axis acceleration data from ADXL345
  - Detects spikes exceeding a defined threshold
  - Sends event messages via Serial to Raspberry Pi
  ------------------------------------------------
  Connections (ADXL345 → Arduino Nano 33 IoT):
    VCC → 3.3V
    GND → GND
    SDA → A4 (SDA)
    SCL → A5 (SCL)
    CS  → 3.3V  (I2C mode)
    SDO → GND
*/

#include <Wire.h>

#define ADXL345_ADDRESS 0x53

// ADXL345 Registers
#define POWER_CTL 0x2D
#define DATA_FORMAT 0x31
#define DATAX0 0x32

float alpha = 0.9;              // Low-pass filter constant
float baselineMag = 0.0;
float threshold = 1.5;          // Adjust based on field testing
unsigned long lastEvent = 0;
const unsigned long debounceMs = 800;  // Minimum delay between events

void setup() {
  Serial.begin(115200);
  Wire.begin();

  // Initialize ADXL345
  writeTo(POWER_CTL, 0x08);     // Measure mode
  writeTo(DATA_FORMAT, 0x08);   // Full resolution, +/-2g
  Serial.println("ADXL345 ready");
}

void loop() {
  int16_t x, y, z;
  readAccel(&x, &y, &z);

  float ax = x * 0.004;  // each LSB = 4mg in full-resolution mode
  float ay = y * 0.004;
  float az = z * 0.004;
  float mag = sqrt(ax*ax + ay*ay + az*az);

  baselineMag = alpha * baselineMag + (1.0 - alpha) * mag;
  float diff = fabs(mag - baselineMag);
  unsigned long now = millis();

  if (diff > threshold && (now - lastEvent) > debounceMs) {
    Serial.print("EVENT,");
    Serial.print(diff, 3);
    Serial.print(",");
    Serial.println(now);
    lastEvent = now;
  }

  delay(10); // ~100 Hz
}

// ---------- Helper Functions ----------
void writeTo(byte address, byte value) {
  Wire.beginTransmission(ADXL345_ADDRESS);
  Wire.write(address);
  Wire.write(value);
  Wire.endTransmission();
}

void readAccel(int16_t *x, int16_t *y, int16_t *z) {
  Wire.beginTransmission(ADXL345_ADDRESS);
  Wire.write(DATAX0);
  Wire.endTransmission(false);
  Wire.requestFrom(ADXL345_ADDRESS, 6, true);

  if (Wire.available() == 6) {
    *x = Wire.read() | (Wire.read() << 8);
    *y = Wire.read() | (Wire.read() << 8);
    *z = Wire.read() | (Wire.read() << 8);
  }
}
