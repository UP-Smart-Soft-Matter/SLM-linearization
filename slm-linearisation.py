import sys
import time
from PIL.Image import fromarray
from matplotlib import pyplot as plt
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import messagebox
import screeninfo
import threading
sys.path.append(r"C:\Users\Mika Music\PycharmProjects\PAX1000-controller")
from pax1000_controller import *

penal = 'VIS-014'
wavelength = 491
retardation = 1 #pi
lower_voltage = 1
upper_voltage = '1,86'
appendix = '_test'


azimuth_over_grayscale = []
max_rotation = np.degrees(retardation * np.pi)

def linear_function(x, max_rotation, max_gs):
    return (max_rotation/max_gs) * x

def init_pax():
    while True:
        try:
            pax = PAX1000()
            return pax
        except Exception:
            messagebox.showerror("Error", "No PAX 1000 found, please connect device and try again")
            continue


class ImageDisplay(tk.Toplevel):
    def __init__(self, monitor: int):
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
        assert isinstance(photo, ImageTk.PhotoImage), "Image must be a PhotoImage object"

        # Update the image in the existing label
        self.label.configure(image=photo)
        self.label.image = photo  # Update the reference to avoid garbage collection

    class NoSecondMonitorError(Exception):
        pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.image_display = ImageDisplay(0)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.__measuring_thread = MeasuringThread()
        self.__measuring_thread.start()
        time.sleep(1)

        self.result = np.empty(256)
        self.counter_gs = 0
        self.counter_cycle = 0

        while self._is_azimuth_none():
            print('PAX1000 starting up')

        self.get_data()

    def close(self):
        with self.__measuring_thread.kill_flag_lock:
            self.__measuring_thread.kill_flag = True
        self.destroy()

    def get_data(self):
        if self.counter_cycle <= 5:
            if self.counter_gs <= 255:
                img = fromarray(np.full((self.image_display.height, self.image_display.width), self.counter_gs, dtype=np.uint8))
                self.image_display.show_image(img)

                with self.__measuring_thread.azimuth_lock:
                    azimuth = self.__measuring_thread.azimuth
                self.result[self.counter_gs] = azimuth

                print(f'cycle {self.counter_cycle+1}/5 measurement {self.counter_gs+1}/256: azimuth = {azimuth}')

                self.counter_gs += 1
                self.after(500, self.get_data)
            else:
                global azimuth_over_grayscale
                azimuth_over_grayscale.append(self.result.copy())
                self.result = np.empty(256)
                self.counter_gs = 0
                self.counter_cycle += 1
                self.after(500, self.get_data)
        else:
            self.close()

    def _is_azimuth_none(self):
        with self.__measuring_thread.azimuth_lock:
            azimuth = self.__measuring_thread.azimuth

        time.sleep(0.2)

        if azimuth is None:
            return True
        else:
            return False



class MeasuringThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.kill_flag = False
        self.kill_flag_lock = threading.Lock()

        self.azimuth = None
        self.azimuth_lock = threading.Lock()

        self.__pax = None

    def run(self):
        self.__pax = init_pax()
        while not self.kill_flag:
            azimuth = self.__pax.measure_azimuth()
            with self.azimuth_lock:
                self.azimuth = azimuth
            time.sleep(0.1)
        self.__pax.close()


app = App()
app.mainloop()

data_mean = np.stack(azimuth_over_grayscale).mean(axis=0)

jumps = []

for i, datapoint in enumerate(data_mean):
    if i < 255:
        if abs(datapoint - data_mean[i + 1]) > 100:
            jumps.append(i)
    datapoint = datapoint - 90 * - 1
    data_mean[i] = datapoint

data_mean[:jumps[0] + 1] = data_mean[0:jumps[0] + 1] + 180
data_mean[jumps[1] + 1:] = data_mean[jumps[1] + 1:] - 180

data_mean = (data_mean * -1) + 180

ls = np.linspace(0,256, 256)

plt.plot(ls, data_mean)
plt.title("Azimuth Over Grayscale")
plt.axhline(y=90, color='r', linewidth=0.4)
plt.axvline(x=128, color='r', linewidth=0.4)
plt.show()

delta_list = linear_function(ls, max_rotation, 255) - data_mean

linearized = linear_function(ls, max_rotation, 255) + delta_list
lut_float = ((linearized / max(linearized)) * 319)
lut = np.empty_like(lut_float)
for i, datapoint in enumerate(lut_float):
    lut[i] = round(datapoint)

plt.plot(ls, lut)
plt.title("lut")
plt.show()

np.savetxt(f"{penal}_{wavelength}nm_9-5_lin-{retardation}pi_{lower_voltage}V-{upper_voltage}V{appendix}.csv", lut , delimiter=",", fmt="%d")

