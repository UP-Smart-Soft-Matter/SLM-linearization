import numpy as np
import matplotlib.pyplot as plt


penal = 'VIS-014'
wavelength = 491
retardation = 1 #pi
lower_voltage = 1
upper_voltage = '1,86'
appendix = '_test'

max_rotation = np.degrees(retardation * np.pi)

def linear_function(x, max_rotation, max_gs):
    return (max_rotation/max_gs) * x

dummy = np.genfromtxt("dummy.txt", delimiter=",")

azimuth_over_grayscale = [dummy, dummy, dummy, dummy, dummy]
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
