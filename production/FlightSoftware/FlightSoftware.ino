#include <Wire.h>
#include <Servo.h>
#include <BMP388_DEV.h>
#include "Arducam_Mega.h"
#include <LSM6DSLSensor.h>
#include <SoftwareSerial.h>

// Buffer size for image data.
#define CAMERA_BUFFER_SIZE 0xff

// XBee radio receiver pin on the Arduino UNO.
const byte rxPin = 10;
// XBee radio transmitter pin.
const byte txPin = 11;

// XBee radio software serial connection. 
SoftwareSerial xbee_radio(txPin, rxPin);

// Camera select pin.
const int cameraPin = 7;
uint8_t imageData = 0;
uint8_t imageDataNext = 0;
// Flag to indicate the start of an image byte stream.
uint8_t headFlag = 0;
// Byte counter.
unsigned int counter = 0;
// Image buffer, limited to 255 bytes.
uint8_t imageBuff[CAMERA_BUFFER_SIZE] = {0};

Arducam_Mega camera(cameraPin);

// Time in milliseconds between the request and capture of an image.
int pictureDelay = 100; 

// BMP388 sensor object to read temperature, pressure, and altitude.
BMP388_DEV bmp388;

// LSM6DSL sensor object to read accelerometer and gyroscope data.
LSM6DSLSensor AccGyr(&Wire, LSM6DSL_ACC_GYRO_I2C_ADDRESS_LOW);

// Sensor Data
float accelX, accelY, accelZ;
float gyroX, gyroY, gyroZ;
float altitude;
float temperature;
float pressure;

// Voltage sensor pin.
const byte voltmeterPin = A0;
float batteryVoltage;

// Controls the servo that retains the rover.
Servo retentionServo;
// Angle at which the servo is set to release the rover.
const int releasedAngle = 10;
// Angle at which the servo retains the rover.
const int retainedAngle = 20;
// Whether or not the rover has been deployed.
bool deployed = false;

// Mode of the flight software, set by the ground station,
// where 0 is idle (rover retained), 1 is telemetry/sensor transmission,
// 2 is ejection and image capture.
byte flightMode = 0;

/**
 * Sets default states for the rover and its components.
*/
void setup() {
    // Open serial communications on the 9600 baud rate.
    Serial.begin(9600);

    // Wait for the serial monitor to open.
    while (!Serial);
    
    // Initialize the XBee radio to communicate with the ground station.
    xbee_radio.begin(9600);
    camera.begin();
    // Assigns the servo to pin 9 on the Arduino.
    retentionServo.attach(9);
    Wire.begin();

    // Default initialization, places the BMP388 into SLEEP_MODE.
    bmp388.begin(); 
    // Set the BMP388 to normal mode with a 1.28 second standby time.
    bmp388.setTimeStandby(TIME_STANDBY_1280MS);
    bmp388.startNormalConversion(); 

    // Initialize the accelerometer and gyroscope.
    AccGyr.begin();
    AccGyr.Enable_X();
    AccGyr.Enable_G();

    // Set the voltmeter pin to input mode; necessary since the voltmeter is an analog sensor.
    pinMode(voltmeterPin, INPUT);

    // Print a message to the serial monitor to indicate that the 
    // Arduino is powered and all components are initialized.
    Serial.write("======Arduino Powered======\n");
}

void loop() {
    // Listen for incoming data from the radio.
    xbee_radio.listen();

    // If there is data available, read the data and set the flight mode.
    while (xbee_radio.available() > 0)
        flightMode = xbee_radio.read();
    Serial.println(flightMode);

    if (flightMode == 0 || deployed) {
        retentionServo.write(releasedAngle);
    } else if (flightMode == 1) {
        retentionServo.write(retainedAngle);

        // Assign the temperature, pressure, and altitude values to the sensor readings.
        bmp388.getMeasurements(temperature, pressure, altitude);
        
        int32_t accelerometer[3];
        int32_t gyroscope[3];
        AccGyr.Get_X_Axes(accelerometer);
        AccGyr.Get_G_Axes(gyroscope);
        // Assign the accelerometer and gyroscope values to the sensor readings.
        accelX = accelerometer[0];
        accelY = accelerometer[1];
        accelZ = accelerometer[2];
        gyroX = gyroscope[0];
        gyroY = gyroscope[1];
        gyroZ = gyroscope[2];

        // Read the value from the voltmeter pin and convert it to a voltage.
        batteryVoltage = analogRead(voltmeterPin) * (11.0 / 430.0);

        // Indicate the start of a normal data packet.
        xbee_radio.write(0xc8);
        // Nominal status.
        xbee_radio.write(0x01);
        // Mark separation between values.
        xbee_radio.write(0xc9);
        xbee_radio.print(accelX);
        xbee_radio.write(0xc9); 
        xbee_radio.print(accelY); 
        xbee_radio.write(0xc9);
        xbee_radio.print(accelZ);
        xbee_radio.write(0xc9); 
        xbee_radio.print(gyroX);
        xbee_radio.write(0xc9); 
        xbee_radio.print(gyroY);
        xbee_radio.write(0xc9); 
        xbee_radio.print(gyroZ);
        xbee_radio.write(0xc9); 
        xbee_radio.print(temperature); 
        xbee_radio.write(0xc9); 
        xbee_radio.print(pressure); 
        xbee_radio.write(0xc9); 
        xbee_radio.print(batteryVoltage); 
        xbee_radio.write(0xc9); 
        xbee_radio.print(altitude);
        // Indicate the end of a normal data packet.
        xbee_radio.write(0xca);
    } else if (flightMode == 2) {
        delay(1000);
        
        retentionServo.write(releasedAngle);

        delay(pictureDelay);

        // Capture image in JPG format using an image resolution of one of the following: QQVGA, QVGA, VGA, HD, FHD.
        camera.takePicture(CAM_IMAGE_MODE_QVGA, CAM_IMAGE_PIX_FMT_JPG);

        // Indicate the start of an image data packet.
        xbee_radio.write(0xcb);
        
        // Read the image data from the camera.
        while (camera.getReceivedLength()) {
            imageData = imageDataNext;
            imageDataNext = camera.readByte();
            
            // If the image is not being read, then do not write to the buffer.
            if (headFlag == 1) {
                imageBuff[counter++] = imageDataNext;

                // If the buffer is full, write the buffer to the radio.
                if (counter >= CAMERA_BUFFER_SIZE) {
                    xbee_radio.write(imageBuff, counter);
                    // TODO: Remove this line after testing.
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
            if (imageData == 0xff && imageDataNext == 0xd9) {
                // Write the image data to the serial monitor.
                xbee_radio.write(imageBuff, counter);
                // TODO: Remove this line after testing.
                Serial.write(imageBuff, counter);
                counter = 0;
                headFlag = 0;
                flightMode = 0;
                break;
            }
        }
    }
    delay(1000);
}
