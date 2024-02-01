/*
  Software serial test intended for Arduino UNO R3.

  Receives from the two software serial ports, sends to the hardware serial port.

  In order to listen on a software port, you call port.listen().
  When using two software serial ports, you have to switch ports
  by listen()ing on each one in turn. Pick a logical time to switch
  ports, like the end of an expected transmission, or when the
  buffer is empty. This example switches ports when there is nothing
  more to read from a port

  The circuit:
  Two devices which communicate serially are needed.
  * First serial device's TX attached to digital pin 11, RX attached to digital pin 10.
 */
#include <SoftwareSerial.h>

// Receiver pin.
const byte rxPin = 10;
// Transmitter pin.
const byte txPin = 11;

// XBee Radio software serial connection. 
SoftwareSerial xbee_radio(txPin, rxPin);

void setup() {
  // Open serial communications and wait for port to open.
  Serial.begin(9600);

    while (!Serial)
    // Wait for serial port to connect -- necessary for native USB port only.
    ;
  // Output to the serial monitor that the program has initialized.
  Serial.println("Initialized");
  // Start each software serial port with the suggested baud rate.
  xbee_radio.begin(9600);
}

void loop() {
  // By default, the last initialized port is listening. Otherwise, explicitly select it.
  xbee_radio.listen();

  // While there is data being read, send to the serial port.
  while (xbee_radio.available() > 0)
    Serial.println(xbee_radio.read());
  // Send message to the XBee.
  xbee_radio.println("Test");
  // Delay the loop as to not cause a continual spam and to allow other byte receipts.
  delay(100);
}