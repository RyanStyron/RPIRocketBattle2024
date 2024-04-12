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
Mode 5: Default/Terminate Program
'''
flight_modes = {0: b'\x00', 
                1: b'\x01',
                2: b'\x02',
                5: b'\x05'}
# Default flight mode is 5.
flight_mode = 5
# Serial connection to the XBee Radio.
xbee_radio : serial.Serial
# Telemetry data.
telemetry_data = {"altitude": [], "accel-x": [],
                    "accel-y": [], "accel-z": [],
                    "gyro-x": [], "gyro-y": [],
                    "gyro-z": [], "temperature": [],
                    "voltage": []}

def find_xbee_radio() -> None:
    global xbee_radio
    xbee_radio_port = None
    ports = serial.tools.list_ports.comports()
    
    for port in ports:
        # Check if the port is the XBee Radio (USB Serial Port for Windows Machine, USB UART for Mac).
        if 'USB Serial Port' in port.description or 'USB UART' in port.description:
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

def retrieve_telemetry() -> None:
    pass

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
        # Save the image.
        cv.imwrite("production/resources/RoverDeploymentImage.jpeg", img_decode)
    except Exception as err:
        print(f'Other error occurred: {err}')
        print("\nExiting program.")
        exit()

def run_ground_station() -> None:
    global xbee_radio
    global flight_mode
    global telemetry_data

    def update_flight_mode_display() -> None:
        label_display_mode.config(text="Flight Mode " + str(flight_mode))
        root.after(1000, update_flight_mode_display)
    def update_acceleration_display() -> None:
        label_accel.config(text="Accel-X: " + str(telemetry_data["accel-x"][-1]) \
            + ", Accel-Y: " + str(telemetry_data["accel-y"][-1]) \
            + ", Accel-Z: " + str(telemetry_data["accel-z"][-1]) + " (m/s^2)")
        root.after(1000, update_acceleration_display)
    def update_gyro_display() -> None:
        label_gyro.config(text="Gyro-X: " + str(telemetry_data["gyro-x"][-1]) \
            + ", Gyro-Y: " + str(telemetry_data["gyro-y"][-1]) \
            + ", Gyro-Z: " + str(telemetry_data["gyro-z"][-1]) + " (deg/s)")
        root.after(1000, update_gyro_display)
    def update_temperature_display() -> None:
        label_temperature.config(text="Temp (C): " + str(telemetry_data["temperature"][-1]))
        root.after(1000, update_temperature_display)
    def update_voltage_display() -> None:
        label_voltage.config(text="Voltage (V): " + str(telemetry_data["voltage"][-1]))
        root.after(1000, update_voltage_display)
    def confirm_eject() -> None:
        if messagebox.askyesno(title="Ejection Confirmation", message="CONFIRM EJECTION"):
            set_flight_mode(2)
            retrieve_image()
    def confirm_terminate() -> None:
        if messagebox.askyesno(title="Termination Confirmation", message="CONFIRM TERMINATION"):
            set_flight_mode(5)
            store_telemetry_data()
            print("Telemetry stored.\nExiting program.")
            exit()
    def request_telemetry() -> None:
        if flight_mode != 1:
            root.after(1000, request_telemetry)
            pass
        retrieve_telemetry()
        root.after(1000, request_telemetry)
    root = tkinter.Tk()
    root.title("Ground Station")
    root.geometry("300x200")
    
    frame = Frame(root)
    frame.pack()

    label_display_mode = Label(frame, text="Flight Mode " + str(flight_mode), font=("Arial", 12, "bold"))
    label_display_mode.pack()
    label_select_mode = Label(frame, text="Select Flight Mode", font=("Arial", 10, "bold"), fg="red")
    label_select_mode.pack()

    button_mode_0 = tkinter.Button(frame, text="Rover Installation (0)", command=set_flight_mode(0))
    button_mode_0.pack()
    button_mode_1 = tkinter.Button(frame, text="Telemetry Transmission (1)", command=set_flight_mode(1))
    button_mode_1.pack()
    button_mode_2 = tkinter.Button(frame, text="Rover Deployment & Image Capture (2)", command=confirm_eject)
    button_mode_2.pack()
    button_mode_5 = tkinter.Button(frame, text="End Program (5)", command=confirm_terminate)
    button_mode_5.pack()

    graph_altitude = pyplot.Figure()
    graph_altitude_axes = graph_altitude.add_subplot(111)
    graph_altitude_axes.set_ylim(0, 1500)
    graph_altitude_axes.set_xlim(0, 100)
    graph_altitude_axes.set_title("Altitude vs Time")
    graph_altitude_axes.set_xlabel("Time (sec)")
    graph_altitude_axes.set_ylabel("Altitude (m)")
    
    graph_altitude_canvas = FigureCanvasTkAgg(graph_altitude, master=root)
    graph_altitude_canvas.draw()
    graph_altitude_canvas.get_tk_widget().pack()

    # to the right of the plot, display the non-altitude telemetry data
    label_telemetry = Label(frame, text="Telemetry Data", font=("Arial", 10, "bold"), fg="red")
    label_telemetry.pack()
    label_accel = Label(frame, text="Accel-X, Accel-Y, Accel-Z (m/s^2)")
    label_accel.pack()
    label_gyro = Label(frame, text="Gyro-X, Gyro-Y, Gyro-Z (deg/s)")
    label_gyro.pack()
    label_temperature = Label(frame, text="Temp (C)")
    label_temperature.pack()
    label_voltage = Label(frame, text="Voltage (V)")
    label_voltage.pack()

    request_telemetry()
    update_flight_mode_display()
    update_acceleration_display()
    update_gyro_display()
    update_temperature_display()
    update_voltage_display()
    
    root.mainloop()

def store_telemetry_data() -> None:
    global telemetry_data
    file = open("production/resources/telemetry_data.txt", "w")

    for key in telemetry_data:
        file.write(key + ": " + str(telemetry_data[key]) + "\n")
    file.close()

if __name__ == "__main__":
    find_xbee_radio()
    run_ground_station()
    # Will only be reached if the user ends the program without properly terminating.
    store_telemetry_data()
    print("Improperly terminated.\nTelemetry stored.\nExiting program.")
    exit()
