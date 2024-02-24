import serial
import cv2
import numpy

# Serial port, initialized with the path to the port and baud rate.
with serial.Serial('/dev/tty.usbmodem11101', 115200) as input_stream:
    try:
        print("Reading from serial port...")

        # Bytes indicating the start of the image.
        image_bytes_start = b'\xff\xd8'
        # Bytes indicating the end of the image.
        image_bytes_end = b'\xff\xd9'

        # Bytes representing the entirety of the image.
        data = image_bytes_start + input_stream.read_until(image_bytes_end)

        # Decode the data into a byte array, then as an numpy array object.
        image = numpy.asarray(bytearray(data), dtype = "uint8")
        # Send the numpy array object to an opencv Mat object
        img_decode = cv2.imdecode(image, cv2.IMREAD_COLOR)
        
        # Display the image in a window.
        cv2.imshow("Rover Deployment", img_decode)
        # Wait for a key press.
        k = cv2.waitKey(1)

        # If 's' is the key pressed, save the image to the current directory.
        if k == ord("s"):
            cv2.imwrite("RoverDeployment.jpg", img_decode)
    except Exception as err:
        print(f'Error:\n{err}')
