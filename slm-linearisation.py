import sys
import time
from PIL.Image import fromarray
sys.path.append(r"C:\Users\Mika Music\PycharmProjects\PAX1000-controller")
from pax1000_controller import *
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import messagebox
import screeninfo
import threading


azimuth_over_grayscale = None


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

        self.result = np.empty((256,2))
        self.counter = 0

        self.get_data()

    def close(self):
        with self.__measuring_thread.kill_flag_lock:
            self.__measuring_thread.kill_flag = True
        print(self.result)
        self.destroy()

    def get_data(self):
        img = fromarray(np.full((self.image_display.height, self.image_display.width), self.counter, dtype=np.uint8))
        self.image_display.show_image(img)

        with self.__measuring_thread.azimuth_lock:
            azimuth = self.__measuring_thread.azimuth or 0
        self.result[self.counter][0] = self.counter
        self.result[self.counter][1] = azimuth
        self.counter += 1

        if self.counter <= 255:
            self.after(500, self.get_data)
        else:
            global azimuth_over_grayscale
            azimuth_over_grayscale = self.result
            self.close()


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
print(azimuth_over_grayscale)




