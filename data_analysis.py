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

m1 = np.genfromtxt("test_data/raw_data_cycle1.csv", delimiter=",")
m2 = np.genfromtxt("test_data/raw_data_cycle2.csv", delimiter=",")
m3 = np.genfromtxt("test_data/raw_data_cycle3.csv", delimiter=",")
m4 = np.genfromtxt("test_data/raw_data_cycle4.csv", delimiter=",")
m5 = np.genfromtxt("test_data/raw_data_cycle5.csv", delimiter=",")

azimuth_over_grayscale = [m1, m2, m3, m4, m5]

for data in azimuth_over_grayscale:
    for i, datapoint in enumerate(data[:21]):
        if datapoint < 0:
            data[i] = datapoint + 180
    for i, datapoint in enumerate(data[236:]):
        i = i + 236
        if datapoint > 0:
            data[i] = datapoint - 180

data_mean = np.stack(azimuth_over_grayscale).mean(axis=0)
np.savetxt("raw_data_mean.txt", data_mean, fmt='%f')

for i, datapoint in enumerate(data_mean):
    datapoint = (datapoint - 90) * (- 1)
    data_mean[i] = datapoint

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
    lut[i] = abs(round(datapoint))

plt.plot(ls, lut)
plt.title("lut")
plt.show()

np.savetxt(f"{penal}_{wavelength}nm_9-5_lin-{retardation}pi_{lower_voltage}V-{upper_voltage}V{appendix}.csv", lut , delimiter=",", fmt="%d")
