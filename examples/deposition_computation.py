import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gwtransport1d.deposition import compute_concentration, compute_deposition
from gwtransport1d.residence_time import residence_time_retarded

# Flow data
dates = pd.date_range("2020-01-01 23:59:59", periods=400)  # Volume extracted during past day
ddates = (dates[1:] - dates[:-1]) / np.timedelta64(1, "D")  # days

if not (ddates == 1.0).all():
    error_message = "date differences should be equal to 1 day for all elements."
    raise ValueError(error_message)

flow = pd.Series(300.0 * 24, index=dates, name="flow")  # m3
flow[100:200] = 505.0 * 24
flow[200:300] = 83.0 * 24

residence_time_avg = 35.3  # days

u = 1.0  # ng/m2/day

measurements = pd.DataFrame({"flow": flow, "deposition": u})

# Aquifer properties
porosity = 0.3  # dimensionless
thickness = 15.0  # m
retardation_factor = 2.1  # dimensionless

aquifer_pore_volume = measurements.flow.mean() * residence_time_avg  # m3
aquifer_volume = aquifer_pore_volume / porosity  # m3
aquifer_surface_area = aquifer_volume / thickness  # m2

# compute concentration of the compound in the extracted water given the deposition [ng/m3]
modeled_cout = compute_concentration(
    measurements.deposition, measurements.flow, aquifer_pore_volume, porosity, thickness, retardation_factor
)

# compute deposition given the added concentration of the compound in the extracted water [ng/m2/day]
# modeled_deposition should be similar to measurements.deposition
modeled_deposition = compute_deposition(
    modeled_cout, measurements.flow, aquifer_pore_volume, porosity, thickness, retardation_factor
)

# Compute the residence time of the extracted water and retarded by the retardation factor
residence_time = residence_time_retarded(measurements.flow, aquifer_pore_volume, retardation_factor=1.0)
residence_time_r = residence_time_retarded(
    measurements.flow, aquifer_pore_volume, retardation_factor=retardation_factor
)

fig, ax = plt.subplots(2, 1, figsize=(10, 10))
ax[0].plot(modeled_cout.index, modeled_cout, label="Extracted water", color="C0")
ax[0].set_ylabel("Concentration [ng/m3]")
ax[0].legend(loc="upper left")

ax0r = ax[0].twinx()
ax0r.plot(measurements.index, measurements.deposition, label="Measurements", color="C1", marker="o", markevery=(0., 0.1))
ax0r.plot(modeled_deposition.index, modeled_deposition, label="Model", color="C2", marker="*", markevery=(0.05, 0.1))
ax0r.set_ylim(0, 1.2 * measurements.deposition.max())
ax0r.set_ylabel("Deposition [ng/m2/day]")
ax0r.legend(loc="upper right")

ax[1].plot(measurements.index, measurements.flow, label="Volumestroom", color="C0")
ax[1].set_ylabel("Flow [m3/day]")
ax[1].legend(loc="upper left")

ax1r = ax[1].twinx()
ax1r.plot(residence_time, label="Retardation factor 1", color="C1")
ax1r.plot(residence_time_r, label=f"Retardation factor {retardation_factor}", color="C2")
ax1r.set_ylabel("Residence time [days]")
ax1r.legend(loc="upper right")