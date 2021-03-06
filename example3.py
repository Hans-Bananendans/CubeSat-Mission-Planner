"""
example3.py

"Another example how to use the CubeSat-Power-Estimation tool. This example
    shows how instead of using seconds, you can use orbit fractions to
    specify and simulate a mission schedule. In addition, 5 years worth of 
    degradation was applied in the config."

@author: Johan Monster (https://github.com/Hans-Bananendans/)
"""

#%% Import packages
import numpy as np
import pandas as pd

from mission import Mission
from orbit import Orbit

#%% Defining the inputs

# Defining the config
config = {
    "years_passed" : 5, # How many [years] the satellite has been in space for
    
    "battery_capacity" : 81000, # Battery capacity in [W.s] (or: Joule)
    "battery_degradation_factor" : 0.04,
    "battery_init" : 0.5, # 0.5 = Battery begins at 50% charge
    
    "panel_degradation_factor" : 0.02,
    
    "blip_period" : 30, # Currently unused, telemetry blip period
    "blip_duration" : 1, # Currently unused, telemetry blip duration
    "no_blips" : ["downlink"], # Currently unused
    
    "orbital_altitude" : 550 # Orbital altitude in [km]
    }

# List of the names of all used EPS channels.
channels = ["None", "5V_1", "5V_2", "5V_3", "5V_4", "3.3V_1", \
            "3.3V_2", "3.3V_3", "3.3V_4", "Var_rail"]

# Dict of typical voltage supplied to each channel.
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
    
# Dict specifiying which device is on which EPS channel
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

# List of all possible OpStates the satellite can be in.
# This list must be consistent with the specified power.xlsx
state_list = ["idle","recharge","dice_payload","wheel_unloading", \
              "transponder","downlink","safe_mode","recovery_mode", \
              "detumbling_mode"]

# Dict of which colour will be used for each OpState whilst plotting
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

# Fetching the orbital period
to = Orbit(550,97.5,10.5).period()

# Make schedule using orbit segments
schedule3 = {
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

# Loading the power frame, or the device/OpState table
power_frame = pd.read_excel('power.xlsx',index_col=0)

# Loading the two power input vectors, generated by CubeSat-Solar-Estimator
p_sun = np.load("P_sun.npy")
p_alb = np.load("P_alb.npy")


#%% Simulation

# Assembling the mission object
m1 = Mission(config, device_channels, state_list, channels, \
             power_frame, p_sun, p_alb)

# Calling the Mission.propagate() method to start the simulation
# Simulate for 3 orbits and a timestep of 10 seconds.
result = m1.propagate(schedule3, tsim=round(3.0*to,-1), dt=10)


#%% Plotting

# Plotting the power timeline
m1.plot_timeline_power(state_colours)

# Plot a pie graph with the relative power usage of each device
m1.plot_pie_device()

# Plot a timeline of the power usage of each device
m1.plot_timeline_device()

# Plot a timeline of the power on each channel
m1.plot_timeline_channel()

# Plot a timeline of the current on each channel
m1.plot_timeline_channel_currents(channel_voltages)

# Plot a bar graph of the average power consumption on each channel
m1.plot_bar_channel()

# Plot a pie graph of the relative duration of each OpState during the mission
m1.plot_pie_opstate(state_colours)
