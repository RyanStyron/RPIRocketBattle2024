import numpy
import serial
import tkinter
import threading
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
# Ground station GUI root.
root : tkinter.Tk
# Flag to prevent multiple image processing threads.
processing_image = False
# Flag to prevent multiple concurrent telemetry processing threads.
processing_telemetry = False
# Telemetry data.
telemetry_data = {"altitude": [0.0], "accel-x": [0.0],
                    "accel-y": [0.0], "accel-z": [0.0],
                    "gyro-x": [0.0], "gyro-y": [0.0],
                    "gyro-z": [0.0], "temperature": [0.0],
                    "voltage": [0.0]}

class TelemetryReceiver(threading.Thread):
    global root
    global xbee_radio
    global telemetry_data

    def __init__(self) -> None:
        self.telemetry_received = False
        # Daemon thread to prevent the program from waiting for the thread to finish.
        super().__init__(daemon=True)

    def run(self) -> None:
        try:
            print("Parsing for Telemetry...")

            # First bytes sent of a telemetry packet.
            telemetry_start_bytes = b'DBEGIN'
            # Last bytes sent of a telemetry packet.
            telemetry_end_bytes = b'DEND'

            # Read until the start_check bytes are found.
            # These bytes are not part of the telemetry data and are discarded.
            xbee_radio.read_until(telemetry_start_bytes)

            # Read until the end_check bytes are found.
            data = xbee_radio.read_until(telemetry_end_bytes)
            print("Received data:", data)
            data_decoded = data.decode('utf-8')
            print("Decoded data:", data_decoded)

            accel_x = float(data_decoded[data_decoded.find("ACCELX") + 6:data_decoded.find("ACCELY")]) / 1000 * 9.81
            accel_y = float(data_decoded[data_decoded.find("ACCELY") + 6:data_decoded.find("ACCELZ")]) / 1000 * 9.81
            accel_z = float(data_decoded[data_decoded.find("ACCELZ") + 6:data_decoded.find("GYROX")]) / 1000 * 9.81
            gyro_x = float(data_decoded[data_decoded.find("GYROX") + 5:data_decoded.find("GYROY")]) * 180 / 3.14159
            gyro_y = float(data_decoded[data_decoded.find("GYROY") + 5:data_decoded.find("GYROZ")]) * 180 / 3.14159
            gyro_z = float(data_decoded[data_decoded.find("GYROZ") + 5:data_decoded.find("TEMP")])
            temperature = float(data_decoded[data_decoded.find("TEMP") + 4:data_decoded.find("VOLT")])
            voltage = float(data_decoded[data_decoded.find("VOLT") + 4:data_decoded.find("ALT")])
            altitude = float(data_decoded[data_decoded.find("ALT") + 3:data_decoded.find("DEND")])

            telemetry_data["altitude"].append(altitude)
            telemetry_data["accel-x"].append(accel_x)
            telemetry_data["accel-y"].append(accel_y)
            telemetry_data["accel-z"].append(accel_z)
            telemetry_data["gyro-x"].append(gyro_x)
            telemetry_data["gyro-y"].append(gyro_y)
            telemetry_data["gyro-z"].append(gyro_z)
            telemetry_data["temperature"].append(temperature)
            telemetry_data["voltage"].append(voltage)
            self.telemetry_received = True
        except Exception as err:
            store_telemetry_data()
            print(f'Error occurred in telemetry retrieval: {err}')
            print("Telemetry stored.\nExiting program.")
            root.quit()
            exit()

class ImageReceiver(threading.Thread):
    global root
    global xbee_radio

    def __init__(self) -> None:
        self.image_received = False
        self.image_data = None
        # Daemon thread to prevent the program from waiting for the thread to finish.
        super().__init__(daemon=True)

    def run(self) -> None:
        try:
            print("Parsing for Image...")

            # First bytes sent of an image in JPEG format.
            image_start_bytes = b'\xff\xd8'
            # Last bytes sent of an image in JPEG format.
            image_end_bytes = b'\xff\xd9'

            # Read until the start_check bytes are found.
            # These bytes are not part of the image data and are discarded.
            image_preceding_bytes = xbee_radio.read_until(image_start_bytes)

            print("Received start:", image_preceding_bytes)
            # Read until the end_check bytes are found.
            data = image_start_bytes + xbee_radio.read_until(image_end_bytes)

            # Decode the data into a byte array, then an numpy array object.
            self.image_data = numpy.asarray(bytearray(data), dtype="uint8")
            self.image_received = True
        except Exception as err:
            store_telemetry_data()
            print(f'Error occurred in image retrieval: {err}')
            print("Telemetry stored.\nExiting program.")
            root.quit()
            exit()

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
    global processing_image
    
    # If an image is being processed, do not change the flight mode.
    # Upon completion of the image processing, the flight mode will be set to 5.
    if processing_image:
        return False
    if mode is flight_mode:
        return False
    xbee_radio.write(flight_modes[mode])
    flight_mode = mode
    return True

def retrieve_telemetry() -> None:
    global root
    global processing_telemetry

    if not processing_telemetry:
        processing_telemetry = True
        telemetry_receiver = TelemetryReceiver()
        telemetry_receiver.start()

        while not telemetry_receiver.telemetry_received:
            root.update()
        processing_telemetry = False

def retrieve_image() -> None:
    global root
    global xbee_radio
    global processing_image

    # Prevent multiple image processing threads.
    if not processing_image:
        # Set the flight mode to 2 to signal the rover to deploy and capture an image.
        set_flight_mode(2)
        processing_image = True
        image_receiver = ImageReceiver()
        image_receiver.start()

        while not image_receiver.image_received:
            root.update()

        if image_receiver.image_data is not None:
            # Send the numpy array object to an OpenCV Mat object.
            img_decode = cv.imdecode(image_receiver.image_data, cv.IMREAD_COLOR)
            # Display the image.
            cv.imshow("Rover Deployment Image", img_decode)
            # Save the image.
            cv.imwrite("production/resources/RoverDeploymentImage.jpeg", img_decode)
        # Set the flight mode to 5 to signal the end of the image processing.
        set_flight_mode(5)
        processing_image = False

def run_ground_station() -> None:
    global root
    global xbee_radio
    global flight_mode
    global telemetry_data

    def set_flight_mode_0() -> None:
        set_flight_mode(0)
    def set_flight_mode_1() -> None:
        set_flight_mode(1)
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
            # Set the flight mode to 2 to signal the rover to deploy
            # and capture an image (both handled by retrieve_image).
            retrieve_image()
    def confirm_terminate() -> None:
        if messagebox.askyesno(title="Termination Confirmation", message="CONFIRM TERMINATION"):
            set_flight_mode(5)
            store_telemetry_data()
            print("Telemetry stored.\nExiting program.")
            root.quit()
            exit()
    def request_telemetry() -> None:
        if flight_mode != 1:
            root.after(1000, request_telemetry)
        else: 
            retrieve_telemetry()
            graph_altitude_axes.clear()
            graph_altitude_axes.plot(telemetry_data["altitude"][1:])
            graph_altitude_canvas.draw()
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

    button_mode_0 = tkinter.Button(frame, text="Rover Installation (0)", command=set_flight_mode_0)
    button_mode_0.pack()
    button_mode_1 = tkinter.Button(frame, text="Telemetry Transmission (1)", command=set_flight_mode_1)
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
        file.write(key + ": " + str(telemetry_data[key][1:]) + "\n")
    file.close()

if __name__ == "__main__":
    find_xbee_radio()
    run_ground_station()
    # Will only be reached if the user ends the program without properly terminating.
    store_telemetry_data()
    print("Improperly terminated.\nTelemetry stored.\nExiting program.")
    root.quit()
    exit()
