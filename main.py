""" Main loop for mission planning tool prototype """


#%%###### PACKAGE LOGISTICS #########
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.collections as collections
import time

from orbit import Orbit
from opstate import OpState
from mission import Mission


config = {
    "years_passed" : 0,
    
    "battery_capacity" : 81000,
    "battery_degradation_factor" : 0.04,
    "battery_init" : 0.5,
    
    "panel_degradation_factor" : 0.02,
    
    "blip_period" : 30,
    "blip_duration" : 1,
    "no_blips" : ["downlink"],
    
    "orbital_altitude" : 550
    }

channels = ["None", "5V_1", "5V_2", "5V_3", "5V_4", "3.3V_1", \
            "3.3V_2", "3.3V_3", "3.3V_4", "Var_rail"]

channel_voltages = {
    "5V_1" : 5, 
    "5V_2" : 5, 
    "5V_3" : 5, 
    "5V_4" : 5, 
    "3.3V_1" : 3.3,
    "3.3V_2" : 3.3,
    "3.3V_3" : 3.3,
    "3.3V_4" : 3.3,
    "Var_rail" : 6.5 # Can between 6.5-8 VDC, highest current is at 6.5V
    }
    
device_channels = {
    "adcs"              : "5V_4",
    "payload_dice"      : "5V_3",
    "payload_bitflip"   : "3.3V_3",
    "antenna"           : "3.3V_4",
    "obc"               : "5V_2",
    "obc_board"         : "5V_2",
    "rx"                : "Var_rail",
    "tx"                : "Var_rail",
    "eps"               : "None",
    "sensors_1"         : "3.3V_2",
    "sensors_2"         : "3.3V_4",
    }

schedule1 = {
    0       : "dice_payload",
    50      : "transponder",
    100     : "recharge"
    }

schedule2 = {
    0       : "idle",
    1000    : "recharge",
    2000    : "dice_payload",
    3000    : "wheel_unloading",
    4000    : "transponder",
    5000    : "downlink",
    6000    : "safe_mode",
    7000    : "recovery_mode",
    8000    : "detumbling_mode",
    9000    : "idle"
    }

to = Orbit(550,97.5,10.5).period()

schedule3 = {
    0                   : "idle",
    round(0.32*to,-1)   : "transponder",
    round(0.68*to,-1)   : "idle",
    round(1.32*to,-1)   : "transponder",
    round(1.68*to,-1)   : "idle",
    round(2.32*to,-1)   : "transponder",
    round(2.68*to,-1)   : "idle",
    }

schedule4 = {
    0                   : "idle",
    round(0.05*to,-1)   : "recharge",
    round(0.32*to,-1)   : "transponder",
    round(0.68*to,-1)   : "idle",
    round(0.94*to,-1)   : "downlink",
    round(1.10*to,-1)   : "idle",
    round(1.32*to,-1)   : "transponder",
    round(1.68*to,-1)   : "idle",
    round(2.32*to,-1)   : "transponder",
    round(2.68*to,-1)   : "idle",
    }

state_list = ["idle","recharge","dice_payload","wheel_unloading", \
              "transponder","downlink","safe_mode","recovery_mode", \
              "detumbling_mode"]
    
state_colours = ["idle","recharge","dice_payload","wheel_unloading", \
              "transponder","downlink","safe_mode","recovery_mode", \
              "detumbling_mode"]
    
state_colours = {
    "idle"              : "#ffffff",
    "recharge"          : "#2ca02c",
    "dice_payload"      : "#8000ff",
    "wheel_unloading"   : "#0080ff",
    "transponder"       : "#ff8000",
    "downlink"          : "#ff0000",
    "safe_mode"         : "#4000ff",
    "recovery_mode"     : "#777777", 
    "detumbling_mode"   : "#ff00ff"
    }

power_frame = pd.read_excel('power.xlsx',index_col=0)

p_sun = np.load("P_sun.npy")
p_alb = np.load("P_alb.npy")

m1 = Mission(config, device_channels, state_list, channels, \
             power_frame, p_sun, p_alb)

# test = m1.propagate(schedule3, tsim=round(3.0*to,-1), dt=10)
test = m1.propagate(schedule2, tsim=10000, dt=10)
test = m1.sim_data

#%% Plotting

m1.plot_pie_device()
m1.plot_timeline_device()
m1.plot_timeline_channel()
m1.plot_timeline_channel_currents(channel_voltages)
m1.plot_bar_channel()

m1.plot_timeline_power(state_colours)
m1.plot_pie_opstate(state_colours)