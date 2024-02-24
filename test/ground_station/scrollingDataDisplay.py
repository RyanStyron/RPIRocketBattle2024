import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np

# Function to update the plot
def update_plot():
    global data
    global max_data_points

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

    # Schedule the next update after 500 milliseconds (0.5 seconds)
    root.after(500, update_plot)


# Example data
data = []
max_data_points = 30  # Define the maximum number of data points to be plotted

# Create the Tkinter window
root = tk.Tk()
root.title("Real-time Plot")

# Create a Matplotlib figure and add a subplot
fig, ax = plt.subplots()
ax.set_xlabel('Time')
ax.set_ylabel('Value')

# Create a canvas widget to embed the Matplotlib plot in the Tkinter window
canvas = FigureCanvasTkAgg(fig, master=root)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack()

# Initial plot update
update_plot()

# Start the Tkinter event loop
root.mainloop()
