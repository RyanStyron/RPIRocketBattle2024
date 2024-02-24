import serial
import cv2 as cv
import numpy as np

arduino = serial.Serial('/dev/tty.usbmodem11101', 115200) # change to your serial port
settings = arduino.get_settings()

try:
    '''# send_trigger is the last text arduino sends while setting up. This means it's buffer will be empty.
    send_trigger = b'OV5642 detected.\r\n'
    temp = arduino.read_until(send_trigger)

    print("Send Acq Request")

    # Send /x10 (hex 10 = 16 dec) to trigger an image acquisition
    arduino.write(bytes.fromhex("10"))'''

    print("reading")

    # start_check is the first bytes sent for the picture in JPEG format.
    # Read and clear everything sent leading up to that.
    start_check = b'\xff\xd8'
    temp = arduino.read_until(start_check)

    # end_check are the last bytes sent for the picture.
    # since start_check will be read (and cleared from the buffer) you need to add it to the start of the data stream.
    end_check = b'\xff\xd9'
    data = start_check + arduino.read_until(end_check)

    # decode the data into a byte array, then an numpy array object
    image = np.asarray(bytearray(data), dtype="uint8")
    # Send the numpy array object to an opencv Mat object
    img_decode = cv.imdecode(image, cv.IMREAD_COLOR)
    cv.imshow("Display window", img_decode)
    k = cv.waitKey(0)
    if k == ord("s"):
        cv.imwrite(["myImage"], img_decode)

except Exception as err:
    print(f'Other error occurred: {err}')
