#include <WiFiNINA.h>
#include <Wire.h>
#include <BH1750.h>

char ssid[] = "Abhyuday_iPhone";  // Your WiFi name
char pass[] = "1234567890";      // Your WiFi password
char HOST_NAME[] = "maker.ifttt.com";
String KEY = "jQFKR3UB3-QXBW-n_JIPVqNY3WUhIEc2rSpkl21ZBxB";  // Your IFTTT key
WiFiClient client;

BH1750 lightMeter;
const float SUNLIGHT_THRESHOLD = 500.0;  // lux threshold, adjust as needed
bool inSunlight = false;  // Track state
unsigned long lastCheck = 0;
const unsigned long CHECK_INTERVAL = 10000;  // Check every 10 seconds

void setup() {
  Serial.begin(9600);
  while (!Serial);  // Wait for Serial (optional for debug)
  Wire.begin();
  if (!lightMeter.begin()) {
    Serial.println("BH1750 not detected!");
    while (1);  // Halt if sensor fails
  }
  Serial.println("BH1750 initialized");

  // Connect to WiFi with retry
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 6) {
    Serial.print("Connecting to ");
    Serial.println(ssid);
    WiFi.begin(ssid, pass);
    delay(5000);
    attempts++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi connected! IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("WiFi connection failed!");
  }
}

void loop() {
  if (millis() - lastCheck > CHECK_INTERVAL) {
    lastCheck = millis();
    float lux = lightMeter.readLightLevel();
    Serial.print("Light: ");
    Serial.print(lux, 1);
    Serial.println(" lx");

    if (lux > SUNLIGHT_THRESHOLD && !inSunlight) {
      inSunlight = true;
      sendIFTTTEvent("sunlight_start");
    } else if (lux <= SUNLIGHT_THRESHOLD && inSunlight) {
      inSunlight = false;
      sendIFTTTEvent("sunlight_stop");
    }
  }
}

void sendIFTTTEvent(String event) {
  Serial.print("Attempting to send event: ");
  Serial.println(event);
  int retries = 0;
  while (retries < 3 && !client.connect(HOST_NAME, 80)) {
    Serial.println("Connection attempt failed, retrying...");
    delay(1000);
    retries++;
  }

  if (client.connected()) {
    String path = "/trigger/" + event + "/with/key/" + KEY;
    client.print("GET ");
    client.print(path);
    client.println(" HTTP/1.1");
    client.println("Host: maker.ifttt.com");
    client.println("User-Agent: ArduinoNano33IoT");
    client.println("Connection: close");
    client.println();
    delay(2000);  // Wait for response
    while (client.connected()) {
      if (client.available()) {
        String response = client.readString();
        Serial.println("IFTTT Response: " + response.substring(0, 100));  // First 100 chars
      }
    }
    client.stop();
    Serial.println("Event sent: " + event);
  } else {
    Serial.println("Failed to connect to IFTTT after retries.");
  }
}
