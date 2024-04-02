import serial
import cv2 as cv
import numpy as np
import serial.tools.list_ports

# Device port of the XBee Radio.
xbee_radio_port = None
# All used ports on the device.
ports = serial.tools.list_ports.comports()

# Assign the port of the XBee Radio.
for port in ports:
    if 'USB Serial Port' in port.description:
        xbee_radio_port = port.device
        break
if xbee_radio_port is None:
    print("XBee Radio not found.")
    exit()
else:
    print("XBee Radio found.\n")

# Open the serial connection to the XBee Radio on the 9600 baud rate.
xbee_radio = serial.Serial(xbee_radio_port, 9600)

try:
    # Force the radio to mode zero then mode two for image capture.
    xbee_radio.write(b'\x00')
    xbee_radio.write(b'\x02')

    print("Reading...")

    # start_check represents the first bytes sent of an image in JPEG format.
    # Read and clear everything sent leading up to that.
    start_check = b'\xff\xd8' 
    # end_check represents the last bytes sent of an image in JPEG format.
    end_check = b'\xff\xd9'

    # Read until the start_check bytes are found.
    temp = xbee_radio.read_until(start_check)
    
    print("start_check:", temp)
    # Read until the end_check bytes are found.
    data = start_check + xbee_radio.read_until(end_check)

    # Decode the data into a byte array, then an numpy array object.
    image = np.asarray(bytearray(data), dtype="uint8")
    # Send the numpy array object to an OpenCV Mat object.
    img_decode = cv.imdecode(image, cv.IMREAD_COLOR)
    # Display the image.
    cv.imshow("Rover Deployment Image", img_decode)
    # Wait for a key press.
    key = cv.waitKey(0)

    # If the 's' key is pressed, save the image as a file in the resources folder.
    if key == ord("s"):
        cv.imwrite("production/resources/RoverDeploymentImage.jpeg", img_decode)
except Exception as err:
    print(f'Other error occurred: {err}')