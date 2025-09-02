const uint8_t SOIL_PIN = 2;
const uint8_t LDR_PIN  = 3;
const uint8_t LED1_PIN = 8;
const uint8_t LED2_PIN = 9;

volatile bool soilFlag = false;
volatile bool ldrFlag = false;
volatile bool led1State = false;
volatile bool led2State = false;

// ISRs (keep them short)
void soilISR() {
  soilFlag = true;
}

void ldrISR() {
  ldrFlag = true;
}

void setup() {
  Serial.begin(115200);
  delay(200);

  // Pin setup
  pinMode(SOIL_PIN, INPUT); // Soil sensor DOUT
  pinMode(LDR_PIN, INPUT);  // LDR sensor DOUT
  pinMode(LED1_PIN, OUTPUT);
  pinMode(LED2_PIN, OUTPUT);
  digitalWrite(LED1_PIN, LOW);
  digitalWrite(LED2_PIN, LOW);

  // Attach interrupts
  // Use CHANGE to detect both edges, or RISING/FALLING if you only want one
  attachInterrupt(digitalPinToInterrupt(SOIL_PIN), soilISR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(LDR_PIN), ldrISR, CHANGE);

  Serial.println("System ready. Soil->D2, LDR->D3, LED1->D8, LED2->D9");
  Serial.println("Note: Adjust module thresholds with potentiometer if needed.");
}

void loop() {
  // Handle soil event
  if (soilFlag) {
    noInterrupts();
    soilFlag = false;
    interrupts();

    int s = digitalRead(SOIL_PIN); // current soil state
    led1State = !led1State;        // toggle LED1 each event
    digitalWrite(LED1_PIN, led1State);

    Serial.print("Soil event: D2=");
    Serial.print(s);
    Serial.print(" -> LED1=");
    Serial.println(led1State ? "ON" : "OFF");
  }

  // Handle LDR event
  if (ldrFlag) {
    noInterrupts();
    ldrFlag = false;
    interrupts();

    int l = digitalRead(LDR_PIN); // current LDR state
    led2State = !led2State;       // toggle LED2 each event
    digitalWrite(LED2_PIN, led2State);

    Serial.print("LDR event: D3=");
    Serial.print(l);
    Serial.print(" -> LED2=");
    Serial.println(led2State ? "ON" : "OFF");
  }

  // Tiny delay to avoid flooding Serial
  delay(5);
}
