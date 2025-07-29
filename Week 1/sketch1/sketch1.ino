const int buttonPin = 9;           // Button input pin
const int ledPin = LED_BUILTIN;    // Built-in LED pin

void setup() {
  pinMode(ledPin, OUTPUT);
  pinMode(buttonPin, INPUT);
}

void loop() {
  if (digitalRead(buttonPin) == HIGH) {  
    blinkNameInMorse();
    delay(2000);  // Wait before repeating
  }
}

void dot() {
  digitalWrite(ledPin, HIGH);
  delay(200);
  digitalWrite(ledPin, LOW);
  delay(200);
}

void dash() {
  digitalWrite(ledPin, HIGH);
  delay(600);
  digitalWrite(ledPin, LOW);
  delay(200);
}

void blinkLetter(char letter) {
  switch (letter) {
    case 'A': dot(); dash(); break;
    case 'B': dash(); dot(); dot(); dot(); break;
    case 'D': dash(); dot(); dot(); break;
    case 'E': dot(); break;
    case 'H': dot(); dot(); dot(); dot(); break;
    case 'I': dot(); dot(); break;
    case 'L': dot(); dash(); dot(); dot(); break;
    case 'N': dash(); dot(); break;
    case 'T': dash(); break;
    case 'U': dot(); dot(); dash(); break;
    case 'Y': dash(); dot(); dash(); dash(); break;
  }
  delay(600);  // Space between letters
}

void blinkNameInMorse() {
  // Blink ABHYUDAY
  blinkLetter('A');
  blinkLetter('B');
  blinkLetter('H');
  blinkLetter('Y');
  blinkLetter('U');
  blinkLetter('D');
  blinkLetter('A');
  blinkLetter('Y');

  delay(1400); // Space between words

  // Blink ANTAAL
  blinkLetter('A');
  blinkLetter('N');
  blinkLetter('T');
  blinkLetter('A');
  blinkLetter('A');
  blinkLetter('L');
}