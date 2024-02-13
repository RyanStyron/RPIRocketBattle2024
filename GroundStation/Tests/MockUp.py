import random
import tkinter as tk
from tkinter import Label, Frame, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np


def confirmEject():
    result = messagebox.askyesno(title="Confirmation", message="Are you sure you want to eject the brick? This action cannot be undone.")
    if result:
        eject()


def eject():
    pass

# Function to update the plot and label
def update_plot_and_label():
    global data
    global max_data_points
    global is_nominal

    # Generate a new data point
    new_value = np.random.rand()

    # Append the new data point to the data array
    data.append(new_value)

    # If the data array exceeds max_data_points, remove the oldest data point
    if len(data) > max_data_points:
        del data[0]

    # Clear the current plot
    ax.clear()

    # Plot the data
    ax.plot(data)

    # Draw the plot
    canvas.draw()

    # Update the label text and background color based on the state of is_nominal
    if is_nominal:
        status_label.config(text="Nominal", bg="green", fg="white")
    else:
        status_label.config(text="Anomaly", bg="red", fg="white")

    # Update the values of the integer labels
    for i, value in enumerate(int_values):
        value.set(round(random.random(), 2))  # For demonstration, setting values from 1 to 8

    # Schedule the next update after 500 milliseconds (0.5 seconds)
    root.after(500, update_plot_and_label)


# Example data
data = []
max_data_points = 30  # Define the maximum number of data points to be plotted

is_nominal = True

# Create the Tkinter window with a white background
root = tk.Tk()
root.title("Real-time Plot")
root.configure(bg="white")
root.geometry("1440x700")
root.resizable(False, False)

# Create a label widget to display the status (Nominal or Anomaly)
status_label = Label(root, text="Nominal", bg="green", fg="white", padx=20, pady=10, font=("Helvetica", 35))
status_label.place(relx=0.5, rely=0, anchor="n")

# Create a frame to contain the labels and their respective boxes
label_frame = Frame(root, bg="white")
label_frame.place(relx=0.5, rely=0.1)

# Create a Matplotlib figure and add a subplot with a smaller size
fig, ax = plt.subplots(figsize=(4, 3))  # Adjust the width and height as needed
ax.set_xlabel('Time')
ax.set_ylabel('Value')

# Create a canvas widget to embed the Matplotlib plot in the Tkinter window
canvas = FigureCanvasTkAgg(fig, master=root)
canvas_widget = canvas.get_tk_widget()
canvas_widget.place(relx=0.05, rely=0.1, relwidth=0.45, relheight=0.6)

# Create labels for displaying integers
int_values = [tk.DoubleVar() for _ in range(8)]

# Create boxes with titles and integer labels
box_titles = ["Acc X", "Acc Y", "Acc Z", "Rot X", "Rot Y", "Rot Z", "Temp", "Voltage"]
for i, (title, int_var) in enumerate(zip(box_titles, int_values)):
    box_frame = Frame(label_frame, bg="white", highlightbackground="black", highlightthickness=2)
    box_frame.pack(side="top", padx=10, pady=5, fill="x")

    box_label = Label(box_frame, text=title, font=("Helvetica", 30), bg="white", foreground="black")
    box_label.pack(side="left", padx=5)

    int_label = Label(box_frame, textvariable=int_var, font=("Helvetica", 30), bg="white", foreground="black")
    int_label.pack(side="right", padx=5)

button = tk.Button(root, text="EJECT SEQUENCE", font=("Helvetica", 30), bg='red', command=confirmEject)
button.pack(side="bottom", anchor="s", pady=50)
# Initial plot update
update_plot_and_label()

# Start the Tkinter event loop
root.mainloop()
