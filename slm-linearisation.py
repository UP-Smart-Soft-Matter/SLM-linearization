import sys
import time
from datetime import datetime
from PIL.Image import fromarray
from matplotlib import pyplot as plt
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import messagebox
import screeninfo
import threading
sys.path.append(r"C:\Users\SSMAdmin\PycharmProjects\PAX1000-controller")
from pax1000_controller import *

penal = 'VIS-014'
wavelength = 491
retardation = 2 #pi
lower_voltage = "1,02"
upper_voltage = '1,85'
appendix = f'_{datetime.now().strftime("%Y%m%d_%H%M%S")}'


azimuth_over_grayscale = []
max_rotation = np.degrees((retardation/2) * np.pi)

def linear_function(x, max_rotation, max_gs):
    """
    Computes a linear mapping from a grayscale value to a rotation value.

    Parameters
    ----------
    x : float or array-like
        Grayscale input values.
    max_rotation : float
        Maximum rotation value corresponding to the highest grayscale value.
    max_gs : int or float
        Maximum grayscale range.

    Returns
    -------
    float or array-like
        Linearly mapped rotation values.
    """
    return (max_rotation/max_gs) * x

def init_pax():
    """
    Initializes a connection to a PAX1000 device.

    Repeatedly attempts to create a PAX1000 instance until successful.
    Displays an error dialog if the device is not detected.

    Returns
    -------
    PAX1000
        Initialized PAX1000 controller object.
    """
    while True:
        try:
            pax = PAX1000()
            return pax
        except Exception:
            messagebox.showerror("Error", "No PAX 1000 found, please connect device and try again")
            continue


class ImageDisplay(tk.Toplevel):
    """
    A fullscreen image display window bound to a specific monitor.

    Handles creating a borderless window and updating displayed images.
    """
    def __init__(self, monitor: int):
        """
        Creates a fullscreen display window on the specified monitor.

        Parameters
        ----------
        monitor : int
            Index of the target monitor.
        """
        assert isinstance(monitor, int) and monitor >= 0, "Monitor must be a non-negative integer!"

        super().__init__()

        monitors = screeninfo.get_monitors()


        if len(monitors) <= monitor:
            raise Exception(f"Monitor index {monitor} is out of range. Found {len(monitors)} monitors.")

        # Select the specified monitor
        selected_monitor = monitors[monitor]
        self.width, self.height = selected_monitor.width, selected_monitor.height

        self.geometry(f"{self.width}x{self.height}+{selected_monitor.x}+{selected_monitor.y}")
        self.configure(background='black')

        self.overrideredirect(True)

        # Initialize the label to None
        self.label = None

    def show_image(self, image_object):
        """
        Displays a PIL image in the window.

        Parameters
        ----------
        image_object : PIL.Image.Image
            Image object to display in the window.
        """
        assert isinstance(image_object, Image.Image), "Image must be a PIL Image object"

        photo = ImageTk.PhotoImage(image_object)

        if self.label is None:
            # Create a label to hold the image
            self.label = tk.Label(self, image=photo)
            self.label.image = photo  # Keep a reference to avoid garbage collection
            self.label.pack()
        else:
            self.__update_image(photo)

    def __update_image(self, photo):
        """
        Updates the displayed image with a new PhotoImage.

        Parameters
        ----------
        photo : ImageTk.PhotoImage
            Updated image to replace the current one.
        """
        assert isinstance(photo, ImageTk.PhotoImage), "Image must be a PhotoImage object"

        # Update the image in the existing label
        self.label.configure(image=photo)
        self.label.image = photo  # Update the reference to avoid garbage collection

    class NoSecondMonitorError(Exception):
        """
        Raised when the requested monitor index does not exist.
        """
        pass


class App(tk.Tk):
    """
    Main application controlling image projection and PAX1000 measurements.

    Generates grayscale images, displays them, collects azimuth data,
    and manages measurement cycles.
    """
    def __init__(self):
        """
        Initializes the application window, measurement thread,
        and dataset structures, then begins the measurement routine.
        """
        super().__init__()
        self.image_display = ImageDisplay(1)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.__measuring_thread = MeasuringThread()
        self.__measuring_thread.start()
        self.__rep_rate = 100
        time.sleep(1)

        self.result = np.empty(256)
        self.counter_gs = 0
        self.counter_cycle = 0

        print('PAX1000 starting up')
        while self._is_azimuth_none():
            pass

        self.get_data(self.__rep_rate)

    def close(self):
        """
        Stops the measurement thread and closes the application window.
        """
        with self.__measuring_thread.kill_flag_lock:
            self.__measuring_thread.kill_flag = True
        self.destroy()

    def get_data(self, rep_rate):
        """
        Runs measurement cycles by projecting grayscale images and
        recording corresponding azimuth values.

        Parameters
        ----------
        rep_rate : int
            Time delay between measurements in milliseconds.
        """
        if self.counter_cycle < 5:
            if self.counter_gs <= 255:
                img = fromarray(np.full((self.image_display.height, self.image_display.width), self.counter_gs, dtype=np.uint8))
                self.image_display.show_image(img)

                with self.__measuring_thread.azimuth_lock:
                    azimuth = self.__measuring_thread.azimuth
                self.result[self.counter_gs] = azimuth

                print(f'cycle {self.counter_cycle+1}/5 measurement {self.counter_gs+1}/256: azimuth = {azimuth}')

                self.counter_gs += 1
                self.after(rep_rate, self.get_data, self.__rep_rate)
            else:
                global azimuth_over_grayscale
                azimuth_over_grayscale.append(self.result.copy())
                np.savetxt(f"raw_data_cycle{self.counter_cycle+1}.csv", self.result, fmt='%f')
                self.result = np.empty(256)
                self.counter_gs = 0
                self.counter_cycle += 1
                self.after(rep_rate, self.get_data, self.__rep_rate)
        else:
            self.close()

    def _is_azimuth_none(self):
        """
        Checks whether the measurement thread has initialized azimuth values.

        Returns
        -------
        bool
            True if azimuth is still None, otherwise False.
        """
        with self.__measuring_thread.azimuth_lock:
            azimuth = self.__measuring_thread.azimuth

        time.sleep(0.2)

        if azimuth is None:
            return True
        else:
            return False



class MeasuringThread(threading.Thread):
    """
    Thread that continuously polls azimuth values from the PAX1000 device.

    Stores the latest reading and stops when the kill flag is set.
    """
    def __init__(self):
        """
        Initializes the measuring thread and required synchronization locks.
        """
        super().__init__()
        self.kill_flag = False
        self.kill_flag_lock = threading.Lock()

        self.azimuth = None
        self.azimuth_lock = threading.Lock()

        self.__pax = None

    def run(self):
        """
        Connects to the PAX1000 and continuously updates the azimuth value
        until the kill flag is triggered.
        """
        self.__pax = init_pax()
        while not self.kill_flag:
            azimuth = self.__pax.measure()["azimuth"]
            with self.azimuth_lock:
                self.azimuth = azimuth
        self.__pax.close()


app = App()
app.mainloop()

# Post-measurement data processing

# Adjust negative azimuth values at the start and positive azimuth values at the end
for data in azimuth_over_grayscale:
    # Correct first 20 datapoints if they are negative
    for i, datapoint in enumerate(data[:21]):
        if datapoint < 0:
            data[i] = datapoint + 180
    # Correct last 20 datapoints if they are positive
    for i, datapoint in enumerate(data[236:]):
        i = i + 236
        if datapoint > 0:
            data[i] = datapoint - 180

# Compute the mean azimuth over all measurement cycles
data_mean = np.stack(azimuth_over_grayscale).mean(axis=0)
# Save mean data to a text file
np.savetxt("raw_data_mean.txt", data_mean, fmt='%f')

# Flip and offset mean data to correct for reference frame
for i, datapoint in enumerate(data_mean):
    datapoint = (datapoint - 90) * (-1)
    data_mean[i] = datapoint

# Create a grayscale axis from 0 to 256
ls = np.linspace(0, 256, 256)

# Plot the mean azimuth vs. grayscale
plt.plot(ls, data_mean)
plt.title("Azimuth Over Grayscale")
plt.axhline(y=90, color='r', linewidth=0.4)  # reference horizontal line
plt.axvline(x=128, color='r', linewidth=0.4)  # reference vertical line
plt.show()

# Calculate deviation from ideal linear function
delta_list = linear_function(ls, max_rotation, 255) - data_mean

# Apply correction to linearize the data
linearized = linear_function(ls, max_rotation, 255) + delta_list

# Scale the linearized data to LUT (0-319) and round to integers
lut_float = ((linearized / max(linearized)) * 319)
lut = np.empty_like(lut_float)
for i, datapoint in enumerate(lut_float):
    lut[i] = abs(round(datapoint))

# Plot the final LUT
plt.plot(ls, lut)
plt.title("lut")
plt.show()

# Save LUT to CSV with naming format including wavelength, voltage, and appendix
np.savetxt(f"{penal}_{wavelength}nm_9-5_lin-{retardation}pi_{lower_voltage}V-{upper_voltage}V{appendix}.csv", lut, delimiter=",", fmt="%d")
