#include <BerryIMU.h>
#include <Wire.h>

BerryIMU berry;

void setup() {
  berry.begin();
  Wire.begin();
}

void loop() {
    // Sensor Values
    float accelX, accelY, accelZ;
    float gyroX, gyroY, gyroZ;
    
    berry.readAccelerometer(&accelX, &accelY, &accelZ);
    berry.readGyroscope(&gyroX, &gyroY, &gyroZ);

    // Outputting acceleration values to the serial monitor.
    Serial.print("Acceleration (x, y, z): ");
    Serial.print(accelX); Serial.print(", ");
    Serial.print(accelY); Serial.print(", ");
    Serial.println(accelZ);

    // Outputting gyroscope values (degrees per second) to the serial monitor.
    Serial.print("Angular Velocity (x, y, z): ");
    Serial.print(gyroX); Serial.print(", ");
    Serial.print(gyroY); Serial.print(", ");
    Serial.println(gyroZ);
}