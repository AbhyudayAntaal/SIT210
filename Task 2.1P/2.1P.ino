#include <WiFiNINA.h>
#include "DHT.h"

#define DHTTYPE DHT11
#define DHTPIN 2       // DHT data pin

DHT dht(DHTPIN, DHTTYPE);

char ssid[] = "Abhyuday";           // WiFi SSID
char pass[] = "Antaal@2024";        // WiFi Password
WiFiClient client;

unsigned long channelID = 3032171;  // Your ThingSpeak channel ID
const char *writeAPIKey = "Q4EK7E9L4ANSJQ3G"; // ThingSpeak Write API Key

void setup() {
  Serial.begin(9600);
  dht.begin();

  // Connect to Wi-Fi
  WiFi.begin(ssid, pass);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
}

void loop() {
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("Failed to read from DHT sensor!");
    delay(2000);
    return;
  }

  Serial.print("Temperature: ");
  Serial.print(temperature);
  Serial.print("°C | Humidity: ");
  Serial.print(humidity);
  Serial.println("%");

  // Build POST body in correct ThingSpeak format
  String postStr = "api_key=" + String(writeAPIKey) +
                   "&field1=" + String(temperature, 2) +
                   "&field2=" + String(humidity, 2);

  if (client.connect("api.thingspeak.com", 80)) {
    Serial.println("Connected to ThingSpeak server");
    
    client.print("POST /update HTTP/1.1\r\n");
    client.print("Host: api.thingspeak.com\r\n");
    client.print("Connection: close\r\n");
    client.print("Content-Type: application/x-www-form-urlencoded\r\n");
    client.print("Content-Length: ");
    client.print(postStr.length());
    client.print("\r\n\r\n");
    client.print(postStr);

    Serial.println("Data sent: " + postStr);
  } else {
    Serial.println("Connection to ThingSpeak failed");
  }

  // Read ThingSpeak server response
  unsigned long timeout = millis();
  while (client.connected() && millis() - timeout < 2000) {
    while (client.available()) {
      char c = client.read();
      Serial.write(c);
    }
  }

  client.stop();

  delay(20000); 
