#include "Arducam_Mega.h"

#define  BUFFER_SIZE  0xff

const int CS = 7; // Chip select pin for the camera
uint8_t imageData = 0;
uint8_t imageDataNext = 0;
uint8_t headFlag = 0;
unsigned int i = 0;
uint8_t imageBuff[BUFFER_SIZE] = {0};

Arducam_Mega myCAM(CS);

void setup() {
  Serial.begin(115200);
  myCAM.begin();
}


void loop() {
  delay(3000);
  myCAM.takePicture(CAM_IMAGE_MODE_FHD,CAM_IMAGE_PIX_FMT_JPG); // capture image as JPG using an image resolution of one of the following: QQVGA, QVGA, VGA, HD, FHD
  while (myCAM.getReceivedLength()) {
    imageData = imageDataNext;
    imageDataNext = myCAM.readByte();
    
    if (headFlag == 1) { // if this isn't the end of the file then get the next byte and send the current one
      imageBuff[i++]=imageDataNext;

      if (i >= BUFFER_SIZE) { // check to make sure there is still data to write
        Serial.write(imageBuff, i);
        i = 0;
      }
    }

    if (imageData == 0xff && imageDataNext ==0xd8) { // if this is the start of the file then get the first 2 bytes
      headFlag = 1;
      imageBuff[i++]=imageData;
      imageBuff[i++]=imageDataNext;  
    }

    if (imageData == 0xff && imageDataNext ==0xd9) { // if this is the last byte, send it then break the loop to finish
        headFlag = 0;
        Serial.write(imageBuff, i);
        i = 0;
        break;
    }
  }
  delay(7000);
  //while(true); // uncomment me to only take one picture leave commented to take a picture every 10 secs
}