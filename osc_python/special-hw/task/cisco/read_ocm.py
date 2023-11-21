from matplotlib import pyplot as plt
import asyncio

import json
from drivers.cisco.driver import CiscoEDFA35, CiscoWSS
from pandas import read_csv
from numpy import array, reshape, sum
from time import time, sleep
import numpy as np
from task.osa.osa_switch import OsaSwitch
from osi.tool.conversions import dBm2lin, lin2dBm

with open("../../resources/ML/amplifiers.json", "r") as amp_file:
    amps = json.load(amp_file)

with open("../../resources/configuration/default/wxc.json", "r") as channel_info_file:
    channel_info = json.load(channel_info_file)

with open("../../resources/ML/wxc.json", "r") as wxc_file:
    wxc_info = json.load(wxc_file)

with open("../../resources/ML/ML_variable_spectrum_configurations.csv") as conf_file:
    confs = read_csv(conf_file)

channel_info["freq_step"] = channel_info["freq_step"] / 1e3

wss = CiscoWSS(**wxc_info["mux"])

slices, ocm_mux = wss.get_ocm(port="COM", switch="MUX")
plt.plot(ocm_mux, label='MUX')
print(ocm_mux)

slices, ocm_dmx = wss.get_ocm(port="COM", switch="DMX")
ocm_mux = array(ocm_mux)
ocm_dmx = array(ocm_dmx)
print(slices)
plt.plot(ocm_dmx, label="DMX")
print(ocm_dmx)
plt.legend()
plt.show()
print(len(ocm_dmx), len(ocm_mux))


# boh


ocm_mux = lin2dBm(sum(reshape(dBm2lin(ocm_mux), [96, 8]), 1))
ocm_dmx = lin2dBm(sum(reshape(dBm2lin(ocm_dmx), [96, 8]), 1))

plt.plot(ocm_mux, label='MUX')
print(ocm_mux)

plt.plot(ocm_dmx, label="DMX")
print(ocm_dmx)
plt.legend()
plt.show()
