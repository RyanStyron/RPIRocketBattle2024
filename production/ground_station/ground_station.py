import time
import numpy
import serial
import tkinter
import cv2 as cv
import serial.tools.list_ports
import matplotlib.pyplot as pyplot
from tkinter import Label, Frame, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

'''
Mode 0: Rover Installation
Mode 1: Telemetry Transmission
Mode 2: Rover Deployment & Image Capture
'''
flight_modes = {0: b'\x00', 
                1: b'\x01',
                2: b'\x02' }
# Default flight mode is 5.
flight_mode = 5
# Serial connection to the XBee Radio.
xbee_radio : serial.Serial
# Whether or not the flight is complete.
flight_complete = False

def find_xbee_radio() -> None:
    global xbee_radio
    xbee_radio_port = None
    ports = serial.tools.list_ports.comports()
    
    for port in ports:
        if 'USB Serial Port' in port.description:
            xbee_radio_port = port.device
            break
    if xbee_radio_port is None:
        print("XBee Radio not found. Exiting program.")
        exit()
    else:
        print("XBee Radio found.\n")
    xbee_radio = serial.Serial(xbee_radio_port, 9600)

def set_flight_mode(mode: int) -> bool:
    global flight_mode
    
    if mode == flight_mode:
        return False
    xbee_radio.write(flight_modes[mode])
    flight_mode = mode
    return True

def plot_telemetry() -> None:
    pass

def retrieve_image() -> None:
    global xbee_radio
    
    try:
        # Force the radio to mode zero then mode two for image capture.
        xbee_radio.write(b'\x00')
        xbee_radio.write(b'\x02')

        print("Parsing for Image...")

        # start_check represents the first bytes sent of an image in JPEG format.
        # Read and clear everything sent leading up to that.
        start_check = b'\xff\xd8' 
        # end_check represents the last bytes sent of an image in JPEG format.
        end_check = b'\xff\xd9'

        # Read until the start_check bytes are found.
        temp = xbee_radio.read_until(start_check)
        
        print("Received start:", temp)
        # Read until the end_check bytes are found.
        data = start_check + xbee_radio.read_until(end_check)

        # Decode the data into a byte array, then an numpy array object.
        image = numpy.asarray(bytearray(data), dtype="uint8")
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
        print("\nExiting program.")
        exit()

if __name__ == "__main__":
    find_xbee_radio()
    set_flight_mode(flight_modes[0])

    while not flight_complete:
        if flight_mode == 0:
            # Delay for 1 second, then set flight mode to 1.
            time.sleep(1)
            set_flight_mode(flight_modes[1])
        elif flight_mode == 1:
            plot_telemetry()
        elif flight_mode == 2:
            # Delay for 1 second, then retrieve the image.
            time.sleep(1)
            retrieve_image()

            if b'\nEnd Program\n' in xbee_radio.read_all():
                flight_complete = True
        else:
            print("Invalid flight mode:", flight_mode)