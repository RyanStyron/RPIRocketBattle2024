#include "Arducam_Mega.h"

#define BUFFER_SIZE 0xff

// Chip select pin for the camera.
const int chipSelectPin = 7;
uint8_t imageData = 0;
uint8_t imageDataNext = 0;
uint8_t headFlag = 0;
// Byte counter.
unsigned int counter = 0;
uint8_t imageBuff[BUFFER_SIZE] = {0};

Arducam_Mega camera(chipSelectPin);

void setup() {
  Serial.begin(115200);
  camera.begin();
}

void loop() {
  delay(3000);

  // Capture image in JPG format using an image resolution of one of the following: QQVGA, QVGA, VGA, HD, FHD.
  camera.takePicture(CAM_IMAGE_MODE_FHD, CAM_IMAGE_PIX_FMT_JPG);

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
        Serial.write(imageBuff, counter);
        counter = 0;
        break;
    }
  }
  delay(7000);

  // If uncommented, only one picture will be taken.
  // while(true);
}