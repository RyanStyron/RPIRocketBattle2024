const int servoPin = 9; // Pin connected to the servo

void setup() {
  pinMode(servoPin, OUTPUT);
}

void loop() {
  analogWrite(servoPin, map(0, 0, 180, 544, 2400) / 8); // Convert pulse width to duty cycle (divide by 8)
  delay(250); // Wait for servo to reach the position
  analogWrite(servoPin, map(90, 0, 180, 544, 2400) / 8); // Convert pulse width to duty cycle (divide by 8)
  delay(250); // Wait for servo to reach the position
}
