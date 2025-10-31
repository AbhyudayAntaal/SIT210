#include <Arduino_LSM6DS3.h>

#define VIBRATION_THRESHOLD 0.6
#define SAMPLE_INTERVAL 50

float prevAccelX = 0, prevAccelY = 0, prevAccelZ = 0;

void setup() {
  Serial.begin(9600);
  while (!Serial);

  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }

  Serial.println("IMU initialized!");
  Serial.println("Monitoring for sudden vibrations...");
}

void loop() {
  float accelX, accelY, accelZ;

  if (IMU.accelerationAvailable()) {
    IMU.readAcceleration(accelX, accelY, accelZ);

    float deltaX = abs(accelX - prevAccelX);
    float deltaY = abs(accelY - prevAccelY);
    float deltaZ = abs(accelZ - prevAccelZ);
    float vibrationMagnitude = sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);

    if (vibrationMagnitude > VIBRATION_THRESHOLD) {
      Serial.print("Sudden vibration detected! Magnitude: ");
      Serial.print(vibrationMagnitude);
      Serial.println(" g");
    }

    prevAccelX = accelX;
    prevAccelY = accelY;
    prevAccelZ = accelZ;
  }

  delay(SAMPLE_INTERVAL);
}