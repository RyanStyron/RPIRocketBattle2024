#include <Wire.h>
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
BMP388_DEV temp_press_alt_sensor;

// LSM6DSL sensor object to read accelerometer and gyroscope data.
LSM6DSLSensor accel_gyro_sensor(&Wire, LSM6DSL_ACC_GYRO_I2C_ADDRESS_LOW);

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
const int retentionServoPin = 9;
// Angle at which the servo is set to release the rover.
const int releasedAngle = 10;
// Angle at which the servo retains the rover.
const int retainedAngle = 20;

// Mode of the flight software, set by the ground station,
// where 0 is idle (rover retained), 1 is telemetry/sensor transmission,
// 2 is ejection and image capture. 5 is the default mode, in which nothing occurs.
byte flightMode = 5;

/**
 * Sets default states for the rover and its components.
*/
void setup() {
    // Wait for the serial monitor to open.
    while (!Serial);
 
    // Initialize the XBee radio to communicate with the ground station.
    xbee_radio.begin(9600);
    camera.begin();
    // Set the rentention servo pin to output mode.
    pinMode(retentionServoPin, OUTPUT);
    Wire.begin();

    // Default initialization, places the BMP388 into SLEEP_MODE.
    temp_press_alt_sensor.begin(); 
    // Set the BMP388 to normal mode with a 1.28 second standby time.
    temp_press_alt_sensor.setTimeStandby(TIME_STANDBY_1280MS);
    temp_press_alt_sensor.startNormalConversion(); 

    // Initialize the accelerometer and gyroscope.
    accel_gyro_sensor.begin();
    accel_gyro_sensor.Enable_X();
    accel_gyro_sensor.Enable_G();

    // Set the voltmeter pin to input mode; necessary since the voltmeter is an analog sensor.
    pinMode(voltmeterPin, INPUT);
}

/**
 * Main loop of the flight software after initialization.
*/
void loop() {
    // Listen for incoming data from the radio.
    xbee_radio.listen();

    // If there is data available, read the data and set the flight mode.
    while (xbee_radio.available() > 0)
        flightMode = xbee_radio.read();

    if (flightMode == 0) {
        // Set the servo to the released angle to install the rover.
        analogWrite(retentionServoPin, map(releasedAngle, 0, 180, 544, 2400) / 8);
    } else if (flightMode == 1) {
        // Set the servo to the retained angle.
        analogWrite(retentionServoPin, map(retainedAngle, 0, 180, 544, 2400) / 8);

        // Assign the temperature, pressure, and altitude values to the sensor readings.
        temp_press_alt_sensor.getMeasurements(temperature, pressure, altitude);
        int32_t accelerometer[3];
        int32_t gyroscope[3];
        accel_gyro_sensor.Get_X_Axes(accelerometer);
        accel_gyro_sensor.Get_G_Axes(gyroscope);
        
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
        // Delay for one second as to allow remaining data to be sent.
        delay(1000);
        
        // Set the servo to the released angle to deploy the rover.
        analogWrite(retentionServoPin, map(releasedAngle, 0, 180, 544, 2400) / 8);

        // Delay the capture of an image to allow the rover to deploy.
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
                    counter = 0;
                }
            }

            // Check for the start of the image byte stream.
            if (imageData == 0xff && imageDataNext == 0xd8) {
                headFlag = 1;
                imageBuff[counter++] = imageData;
                imageBuff[counter++] = imageDataNext;  
            }

            // Check for the end of the image byte stream.
            if (imageData == 0xff && imageDataNext == 0xd9) {
                // Write the image data to the serial monitor.
                xbee_radio.write(imageBuff, counter);
                counter = 0;
                headFlag = 0;
                flightMode = 5;
                xbee_radio.print("\nEnd Program\n");
                break;
            }
        }
    }
    // Delay for one second as to not overload the radio.
    delay(1000);
}
