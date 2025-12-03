# SLM-linearization

This project provides Python applications to interface with a **PAX1000** polarimeter to measure azimuth values over grayscale images and generate a linearized **Lookup Table (LUT)** for optical calibration.

There are two main scripts:

* `slm-linearisation.py`: Runs full measurement cycles (5 cycles) across all 256 grayscale values, computes the mean azimuth, and generates a final LUT CSV file.
* `plot_gs_a.py`: Runs a single measurement cycle for verification and testing purposes, allowing you to check the azimuth results against the LUT.

---

## Features

* Connects to a **PAX1000** device and continuously measures azimuth.
* Cycles through 256 grayscale values.
* `slm-linearisation.py` supports multiple cycles (default 5) for averaging.
* Saves raw azimuth data for each cycle as CSV files.
* Computes mean azimuth across cycles and applies corrections.
* Generates a linearized LUT from measured azimuth data.
* `plot_gs_a.py` provides single-cycle measurement and plotting for LUT verification.

---

## Requirements

* Python 3.10+
* Packages:

  * `numpy`
  * `matplotlib`
  * `Pillow`
  * `tkinter`
  * `screeninfo`
* Access to the `pax1000_controller` Python module.

---

## Setup

1. Clone or copy the project files.
2. Ensure the `pax1000_controller` folder is in your Python path or project directory.
3. Install required Python packages, e.g.:

```bash
pip install numpy matplotlib Pillow screeninfo
```

4. Connect the **PAX1000** device to your PC.

---

## How to Use

### `slm-linearisation.py`

1. Open the script.
2. Configure the parameters at the top of the file:

```python
penal = 'VIS-014'
wavelength = 491
retardation = 1  # in multiples of pi
lower_voltage = 1
upper_voltage = '1,86'
appendix = '_test'
```

3. Run the script:

```bash
python slm-linearisation.py
```

The application will:

* Start a measurement thread.
* Measure azimuth for each grayscale value (0–255) across multiple cycles.
* Save raw CSV files for each cycle.
* Compute the mean azimuth and generate the LUT.
* Display plots of mean azimuth and final LUT.

### `plot_gs_a.py`

1. Open the script.
2. Run it to perform a **single cycle** measurement.
3. The script will print azimuth measurements for each grayscale and display a plot to verify the LUT visually.

```bash
python plot_gs_a.py
```

---

## Output Files

* `raw_data_cycleN.csv` – Raw azimuth data for cycle N (only in `slm-linearisation.py`)
* `raw_data_mean.txt` – Mean azimuth values across cycles
* `<penal>_<wavelength>nm_9-5_lin-<retardation>pi_<lower_voltage>V-<upper_voltage>V<appendix>.csv` – Final LUT from `slm-linearisation.py`

`plot_gs_a.py` does not save data by default; it is used for plotting and visual verification.

---

## Project Structure

```
project/
│
├─ slm-linearisation.py      # Full measurement and LUT generation
├─ plot_gs_a.py              # Single-cycle measurement for testing
├─ pax1000_controller/       # Module for interfacing with PAX1000
├─ raw_data_cycle1.csv       # Example raw data files from multiple cycles
├─ raw_data_mean.txt         # Example mean data file
└─ VIS-014_491nm_9-5_lin-1pi_1V-1.86V_test.csv   # Example LUT
```

---

## Notes

* The LUT is generated using a linearization correction derived from measured azimuth values.
* Adjust the `retardation`, voltage range, and wavelength according to your optical setup.
* Measurement cycles and repetition rate can be changed by modifying `counter_cycle` or `__rep_rate` in the `App` class of `slm-linearisation.py`.
* Use `plot_gs_a.py` to verify LUTs before full measurement.
