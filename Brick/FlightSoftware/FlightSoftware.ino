#include <SoftwareSerial.h>
#include <Servo.h>
//#include <BerryIMU.h>
#include <Wire.h>
#include "Arducam_Mega.h"

#define BUFFER_SIZE 0xff

const byte rxPin = 10; // Receiver pin.
const byte txPin = 11; // Transmitter pin.

SoftwareSerial xbee_radio(txPin, rxPin); // XBee Radio software serial connection. 

// Chip select pin for the camera.
const int chipSelectPin = 7;
uint8_t imageData = 0;
uint8_t imageDataNext = 0;
uint8_t headFlag = 0;
// Byte counter.
unsigned int counter = 0;
uint8_t imageBuff[BUFFER_SIZE] = {0};

Arducam_Mega camera(chipSelectPin);
int pictureDelay = 100; // Time between deployment and image capture

//BerryIMU berry;
float accelX, accelY, accelZ;
float gyroX, gyroY, gyroZ;
float altitude;
float temperature;

const byte voltageSensor = A0;
float batteryVoltage;

Servo retentionServo;  // create servo object to control a servo
const int releasedAngle = 0; // Defines the angle at which the servo releases the brick
const int retainedAngle = 180; // Defines the angle at which the servo retains the brick
bool deployed = false; // Keeps track of if the brick has been deployed

byte flightMode = 0; // 0 is idle; 1 is pad + flight + landing; 2 is ejection

void setup() {
  Serial.begin(9600); // Open serial communications and wait for port to open.

  while (!Serial) ; // Wait for serial port to connect -- necessary for native USB port only.

  Serial.println("Initialized"); // Output to the serial monitor that the program has initialized.

  xbee_radio.begin(115200); // Start each software serial port with the suggested baud rate.

  camera.begin();

  retentionServo.attach(9);  // attaches the servo on pin 9 to the servo object
  
  //berry.begin();
  Wire.begin();

  pinMode(voltageSensor, INPUT);
}

void loop() {
  xbee_radio.listen(); // By default, the last initialized port is listening. Otherwise, explicitly select it.
  
  while (xbee_radio.available() > 0)
    flightMode = xbee_radio.read();

  if(flightMode == 0 || deployed){
    retentionServo.write(releasedAngle); // keeps servo in deployed position
  } else if(flightMode == 1){
    retentionServo.write(retainedAngle); // locks servo

    //berry.readAccelerometer(&accelX, &accelY, &accelZ); // read accelerion data
    //berry.readGyroscope(&gyroX, &gyroY, &gyroZ); // read rotational data
    batteryVoltage = analogRead(voltageSensor);

    xbee_radio.println(0xc8); // indicate start of normal data packet
    xbee_radio.println(0x01); // nominal status
    xbee_radio.println(0xc9); // mark separation between values
    xbee_radio.println(accelX); // send accelerometer reading
    xbee_radio.println(0xc9); // mark separation between values
    xbee_radio.println(accelY); // send accelerometer reading
    xbee_radio.println(0xc9); // mark separation between values
    xbee_radio.println(accelZ); // send accelerometer reading
    xbee_radio.println(0xc9); // mark separation between values
    xbee_radio.println(gyroX); // send gyro reading
    xbee_radio.println(0xc9); // mark separation between values
    xbee_radio.println(gyroY); // send gyro reading
    xbee_radio.println(0xc9); // mark separation between values
    xbee_radio.println(gyroZ); // send gyro reading
    xbee_radio.println(0xc9); // mark separation between values
    xbee_radio.println(temperature); // send temperature reading
    xbee_radio.println(0xc9); // mark separation between values
    xbee_radio.println(batteryVoltage); // send voltage reading
    xbee_radio.println(0xc9); // mark separation between values
    xbee_radio.println(altitude); // send altitude reading
    xbee_radio.println(0xca); // indicate end of normal data packet
  } else if(flightMode == 2){
    retentionServo.write(releasedAngle); // keeps servo in deployed position

    delay(pictureDelay);

      // Capture image in JPG format using an image resolution of one of the following: QQVGA, QVGA, VGA, HD, FHD.
    camera.takePicture(CAM_IMAGE_MODE_FHD, CAM_IMAGE_PIX_FMT_JPG);
    
    xbee_radio.write(0xcb); // indicate the start of an image data packet
    
    // Read the image data from the camera.
    while (camera.getReceivedLength()) {
      imageData = imageDataNext;
      imageDataNext = camera.readByte();
      
      // If the image is not being read, then do not write to the buffer.
      if (headFlag == 1) {
        imageBuff[counter++] = imageDataNext;

        if (counter >= BUFFER_SIZE) { // check to make sure there is still data to write
          Serial.write(imageBuff, counter);
          counter = 0;
        }
      }

      // Notes the start of the image byte stream.
      if (imageData == 0xff && imageDataNext == 0xd8) {
        headFlag = 1;
        imageBuff[counter++] = imageData;
        imageBuff[counter++] = imageDataNext;  
      }

      // Notes the end of the image byte stream.
      if (imageData == 0xff && imageDataNext ==0xd9) {
          headFlag = 0;
          // Write the image data to the serial monitor.
          xbee_radio.write(imageBuff, counter);
          counter = 0;
          break;
      }
    }
  }
  delay(50);
}
