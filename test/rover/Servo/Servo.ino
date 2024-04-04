// Pin connected to the servo.
const int servoPin = 9;

void setup() {
  pinMode(servoPin, OUTPUT);
}

void loop() {
  // Convert pulse width to duty cycle (divide by 8).
  analogWrite(servoPin, map(0, 0, 180, 544, 2400) / 8); 
  // Wait for servo to reach the position.
  delay(250);
  // Convert pulse width to duty cycle (divide by 8).
  analogWrite(servoPin, map(90, 0, 180, 544, 2400) / 8);
  // Wait for servo to reach the position.
  delay(250);
}
