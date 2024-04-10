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
                2: b'\x02',
                5: b'\x05'}
# Default flight mode is 5.
flight_mode = 5
# Serial connection to the XBee Radio.
xbee_radio : serial.Serial
# Whether or not the flight is complete.
flight_complete = False
# Telemetry data.
telemetry_data = {"altitude": [], "accel-x": 0.0,
                    "accel-y": 0.0, "accel-z": 0.0,
                    "gyro-x": 0.0, "gyro-y": 0.0,
                    "gyro-z": 0.0, "temp": 0.0,
                    "voltage": 0.0}

def find_xbee_radio() -> None:
    global xbee_radio
    xbee_radio_port = None
    ports = serial.tools.list_ports.comports()
    
    for port in ports:
        if 'USB Serial Port' in port.description or 'USB UART' in port.description:
            xbee_radio_port = port.device
            break
    if xbee_radio_port is None:
        print("XBee Radio not found. Exiting program.")
        exit()
    else:
        print("XBee Radio found.\n")
    xbee_radio = serial.Serial(xbee_radio_port, 9600)

def retrieve_image() -> None:
    global xbee_radio
    
    try:
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

def set_flight_mode(mode: int) -> bool:
    global flight_mode
    
    if mode == flight_mode:
        return False
    xbee_radio.write(flight_modes[mode])
    flight_mode = mode
    return True

def run_ground_station() -> None:
    global xbee_radio
    global flight_mode
    global telemetry_data

    def update_flight_mode_display():
        lab_display_mode.config(text="Flight Mode " + str(flight_mode))
        root.after(1000, update_flight_mode_display)
    def set_mode_0():
        set_flight_mode(0)
    def set_mode_1():
        set_flight_mode(1)
    def confirm_eject():
        if messagebox.askyesno(title="Ejection Confirmation", message="CONFIRM EJECTION"):
            set_flight_mode(2)
            retrieve_image()
    def confirm_terminate():
        if messagebox.askyesno(title="Termination Confirmation", message="CONFIRM TERMINATION"):
            set_flight_mode(5)
            exit()
    def retrieve_telemetry():
        if flight_mode != 1:
            root.after(1000, retrieve_telemetry)
            pass

        root.after(1000, retrieve_telemetry)
    root = tkinter.Tk()
    root.title("Ground Station")
    root.geometry("300x200")
    
    frame = Frame(root)
    frame.pack()
    lab_display_mode = Label(frame, text="Flight Mode " + str(flight_mode), font=("Arial", 12, "bold"))
    update_flight_mode_display()
    
    lab_display_mode.pack()
    label_select_mode = Label(frame, text="Select Flight Mode", font=("Arial", 10, "bold"), fg="red")
    label_select_mode.pack()

    button_0 = tkinter.Button(frame, text="Rover Installation (0)", command=set_mode_0)
    button_0.pack()
    button_1 = tkinter.Button(frame, text="Telemetry Transmission (1)", command=set_mode_1)
    button_1.pack()
    button_2 = tkinter.Button(frame, text="Rover Deployment & Image Capture (2)", command=confirm_eject)
    button_2.pack()
    button_5 = tkinter.Button(frame, text="End Program (5)", command=confirm_terminate)
    button_5.pack()

    #TODO: Implement telemetry data retrieval and plot the data.
    retrieve_telemetry()

    # plot telemetry data
    fig = pyplot.Figure()
    ax = fig.add_subplot(111)
    ax.set_ylim(0, 100)
    ax.set_xlim(0, 100)
    ax.set_title("Altitude vs Time")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Altitude (m)")
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack()
    
    root.mainloop()

if __name__ == "__main__":
    find_xbee_radio()
    run_ground_station()