import numpy as np
import matplotlib.pyplot as plt


def linear_function(x, max_rotation, max_gs):
    return (max_rotation/max_gs) * x

azimuth_over_grayscale = np.genfromtxt("data.txt", delimiter=",").T

jumps = []

for i, datapoint in enumerate(azimuth_over_grayscale[1]):
    if i < 255:
        if abs(datapoint - azimuth_over_grayscale[1][i + 1]) > 100:
            jumps.append(i)
    datapoint = datapoint - 90 * - 1
    azimuth_over_grayscale[1][i] = datapoint

azimuth_over_grayscale[1][:jumps[0] + 1] = azimuth_over_grayscale[1][0:jumps[0] + 1] + 180
azimuth_over_grayscale[1][jumps[1] + 1:] = azimuth_over_grayscale[1][jumps[1] + 1:] - 180

azimuth_over_grayscale[1] = (azimuth_over_grayscale[1] * -1) + 180

plt.plot(azimuth_over_grayscale[0], azimuth_over_grayscale[1])
plt.title("Azimuth Over Grayscale")
plt.axhline(y=90, color='r', linewidth=0.4)
plt.axvline(x=128, color='r', linewidth=0.4)
plt.show()

delta_list = linear_function(azimuth_over_grayscale[0], 180, 255) - azimuth_over_grayscale[1]

linearized = linear_function(azimuth_over_grayscale[0], 180, 255) + delta_list
lut_float = ((linearized / max(linearized)) * 319)
lut = np.empty_like(lut_float)
for i, datapoint in enumerate(lut_float):
    lut[i] = round(datapoint)

plt.plot(azimuth_over_grayscale[0], lut)
plt.title("lut")
plt.show()

np.savetxt("VIS-014_491nm_9-5_lin-2pi_1V-1komma86V.csv", lut , delimiter=",", fmt="%d")
