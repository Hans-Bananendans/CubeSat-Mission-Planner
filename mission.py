""" Main loop for mission planning tool prototype """


#%%###### PACKAGE LOGISTICS #########
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.collections as collections
import time
import pandas as pd

from orbit import Orbit
from opstate import OpState

    
class Mission:
    
    def __init__(self, config, device_channels, state_list, \
                 channels, power_frame, p_sun, p_alb):
        
        self.config = config
        self.device_channels = device_channels
        self.state_list = state_list
        self.channels = channels
        
        self.opstates = self.make_opstates(power_frame, config["no_blips"])

        self.batt_cap = config["battery_capacity"] * \
            (1-config["years_passed"]*config["battery_degradation_factor"])
        self.batt_init = config["battery_init"]*self.batt_cap
        self.years_passed = config["years_passed"]
        
        self.blip_period = config["blip_period"]
        self.blip_duration = config["blip_duration"]
        
        self.orbital_altitude = config["orbital_altitude"]
        
        self.dt = None
        self.tsim = None
        self.schedule = None
        
        self.p_sun = p_sun
        self.p_alb = p_alb
        
        # Check internal coherence of given inputs
        self.check_coherence(power_frame)
        
        # Initialize simulation dataframe:
        self.datacols = ["t"] + ["OpState"] + ["p_in", "p_out"] + ["sun"] + \
            ["battery"] + self.channels + list(self.device_channels.keys())
        self.reset_sim_data()
        
    def reset_sim_data(self):
        self.sim_data = pd.DataFrame(columns = self.datacols)
    
    def check_coherence(self, power_frame):
        # Check that power_frame does not contain states not in state_list
        # Check that power_frame does not contain devices not in devices
        # Check that device and device_channels have same number of devices
        # Check that device_channels contains no channels not in channels
    
        # Check if p_sun and p_alb have zeros (if not, no shadow!)
        pass
        
    def make_opstates(self, power_frame, no_blips):
        opstates = {}
        for opstate in self.state_list:
            if opstate in no_blips:
                opstates[opstate] = OpState(power_frame[opstate].to_dict(), \
                                       self.channels, self.device_channels, \
                                       blips_on=0)
            else:                
                opstates[opstate] = OpState(power_frame[opstate].to_dict(), \
                                       self.channels, self.device_channels)
        return opstates
        
    def propagate(self, schedule_unsorted, tsim=10, dt=1):
        self.dt = dt
        self.tsim = tsim
        
        begin = time.time()
        
        # Throw warning if given simulation duration does not cover the
        #   schedule completely.
        if tsim < max(schedule_unsorted.keys()):
            print("\x1b[31mWarning: Schedule is longer than total", \
                      "simulation length! (t_schedule =", \
                      max(schedule_unsorted.keys()), "[s] and t_sim =", \
                      tsim, "[s]) \x1b[0m")
        # TODO: Check that schedule contains no states not in state_list
        # TODO: Throw warning if smallest schedule increment is close to 
        #   chosen dt, and advise to choose a smaller dt or remake the
        #   schedule such that the times are perfect divisors of dt
        
        # Properly setting up input power:
        t_orbit = Orbit(self.orbital_altitude,97.5,10.5).period()
        
        p_sun_ext = np.interp(np.linspace(1,t_orbit,t_orbit), \
                              np.linspace(1,t_orbit,len(self.p_sun)),\
                              self.p_sun)
        p_alb_ext = np.interp(np.linspace(1,t_orbit,t_orbit), \
                              np.linspace(1,t_orbit,len(self.p_alb)),\
                              self.p_alb)
        
        p_in_tot = p_sun_ext + p_alb_ext
    
        # Make schedule iterable by making list of tuples
        schedule = []
        [schedule.append(item) for item in sorted(schedule_unsorted.items())]
        # tuple([(t_i, schedule[t_i]) for t_i in schedule.keys()])
        
        self.schedule = schedule
        
        # Set up the loop
        steps = int(np.ceil(self.tsim/self.dt))
        step = 0
        t = 0
        battery = self.batt_init
        
        opstate_i = 0
        opstate_curr = schedule[opstate_i][1]  # Operation at time 0

        if len(schedule) == 1:
            top_next = tsim
        else:
            top_next = schedule[opstate_i+1][0] # Time when operation will be switched next


        #%%########## SIM LOOP ##############
        while t <= tsim:
            
            # If operation switches during this timestep, update top_next to find 
            # when the next operation switch will take place.
            if t >= top_next:
                if opstate_i == len(schedule)-2:
                    opstate_i += 1
                    top_next = tsim+1  
                else:
                    opstate_i += 1
                    top_next = schedule[opstate_i+1][0]
            
            # Prepare empty line of data entries for this timestep
            data_i = pd.DataFrame(index=[step], columns=self.datacols)
            
            # ==== Current time ====
            data_i.loc[step,"t"] = t
            
            # ==== Currently scheduled operation ====       
            opstate_curr = schedule[opstate_i][1]
            data_i.loc[step,"OpState"] = opstate_curr
            
            # ==== Current total P_in ====
            p_in_curr = p_in_tot[round(t)%len(p_in_tot)]*1000 #Express in mW
            
            # Subtract lifetime degradation
            p_in_curr = p_in_curr * (1-self.config["years_passed"] \
                * self.config["panel_degradation_factor"])
            
            data_i.loc[step,"p_in"] = p_in_curr
            
            # ==== Current total P_out ====
            p_out_curr = self.opstates[opstate_curr].power_used()
            data_i.loc[step,"p_out"] = -p_out_curr
            # Note the minus here, p_out will be logged as negative
            
            # ==== Current sun visibility ====
            if p_in_curr == 0:
                data_i.loc[step,"sun"] = 0
            else:
                data_i.loc[step,"sun"] = 1
            
            
            # ==== Current battery level ====            
            battery += (p_in_curr - p_out_curr)/1000*dt # /1000 'cause mW -> W
            
            # Preventing battery values from going out of bounds
            if battery > self.batt_cap:
                battery = self.batt_cap
            elif battery < 0:
                battery = 0
        
            data_i.loc[step,"battery"] = battery
            
            # ==== Power usage per channel ====
            power_channels = self.opstates[opstate_curr].power_used_channel()
            for channel in power_channels.keys():
                data_i.loc[step,channel] = power_channels[channel]            
            
            # ==== Power usage per device ====
            power_devices = self.opstates[opstate_curr].power_used_device()
            for device in power_devices.keys():
                data_i.loc[step,device] = power_devices[device]
            
            # ==== Concatenate current data line with complete dataframe
            
            self.sim_data = pd.concat([self.sim_data, data_i])
            
            
            # Propagate running variables
            step += 1
            t += dt
        
        runtime = round(time.time()-begin,3)
        print("\x1b[1;30;43m", "Runtime:", runtime, "[s]", "\x1b[0m")
        return self.sim_data
        
    
    def plot_pie_device(self):
        devices = list(self.device_channels.keys())
        
        p_avg_device = []
        for device in devices:
            p_avg_device.append(sum(self.sim_data[device]) \
                                /len(self.sim_data[device]))
        p_perc_device = []
        for i in range(len(devices)):
            p_perc_device.append(p_avg_device[i]/sum(p_avg_device)*100)
        
        # Do plot
        fig1, ax1 = plt.subplots()
        ax1.pie(p_perc_device, labels=devices, autopct='%1.1f%%',
                startangle=90)
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        
        ax1.set_title("Percentage of total power consumption per device during mission")
        plt.show()
        
        return p_avg_device, p_perc_device
    
    
    def plot_timeline_channel(self):
        
        # Filter "None" from channels list
        channels = []
        [channels.append(channel) for channel in self.channels \
            if channel != "None"]
        
        fig1, ax1 = plt.subplots()
        
        for channel in channels:
            if channel == "None":
                pass
            else:
                ax1.plot(self.sim_data["t"], self.sim_data[channel], \
                         label=channel)
        
        ax1.set_xlim(0, self.tsim)
        ax1.set_title('Power consumption over time per channel')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Channel power usage [mW]')

        ax1.legend()
        ax1.grid(True)
    
        
    def plot_timeline_channel_currents(self, channel_voltages):
        
        fig1, ax1 = plt.subplots()
        
        for channel in channel_voltages:
            current = \
                [p/channel_voltages[channel] for p in self.sim_data[channel]]
            ax1.plot(self.sim_data["t"], current, label=channel)
        
        # ax1.plot(self.sim_data["t"], self.sim_data["5V_1"], label="5V_1")
        ax1.set_title('Current in each channel over time')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Channel current [mA]')
        ax1.legend()
        ax1.grid(True)
        
        
    def plot_bar_channel(self):
        
        # Filter "None" from channels list
        channels = []
        [channels.append(channel) for channel in self.channels \
            if channel != "None"]
        
        p_avg_channel = []
        for channel in channels:
            p_avg_channel.append(sum(self.sim_data[channel]) \
                                /len(self.sim_data[channel]))
        
        fig1, ax1 = plt.subplots()
                
        ax1.bar(channels, p_avg_channel, edgecolor='black', linewidth=1)
        ax1.set_xlabel('Channel ID')
        ax1.set_ylabel('Power [mW]')
        ax1.set_title('Average power consumption per channel')
        # ax1.set_xticklabels(labels=channels,rotation=45)
    
        
    def plot_timeline_device(self):
        
        devices = list(self.device_channels.keys())
        
        fig1, ax1 = plt.subplots()
        
        for device in devices:
            ax1.plot(self.sim_data["t"], self.sim_data[device], label=device)
        
        ax1.set_xlim(0, self.tsim)
        ax1.set_title('Power consumption over time per device')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Device power usage [mW]')
        ax1.legend()
        ax1.grid(True)
        
    def plot_timeline_power(self, opstate_colours, show_ops=1):
        
        if not self.schedule:
            raise RuntimeError("Plot cannot be made before a simulation is \
                               completed! Please run the .propagate() method \
                               before continuing!")
        
        fig1, ax1 = plt.subplots(3,1,figsize=(18,9))
        
        # Plot operation history on timeline:
        
        # Remove idle entries from schedule
        rschedule = []
        for i in range(len(self.schedule)):
            # if self.schedule[i][1] != "idle":
            rschedule.append([self.schedule[i][0],self.schedule[i][1]])
        # Add a dummy point beyond the view for line continuity
        rschedule.append([self.tsim*1.01,"dummy"])
        
        # Fetch x_coordinates
        xcoors = []
        for i in range(len(rschedule)):
            xcoors.append(rschedule[i][0])
        # Generate y_coordinates as zeroes
        ycoors = [0]*len(xcoors)
        
        # Plot fat middle line with points
        ax1[0].plot(xcoors, ycoors, "-o",
                color="k", markerfacecolor="w")
        
        # Plot line labels
        for i in range(len(xcoors)):
            ax1[0].annotate(rschedule[i][1], \
                            xy=(xcoors[i], 0), \
                            xytext=(xcoors[i], 0.15), \
                            fontsize=16, \
                            rotation=90, \
                            rotation_mode='anchor', \
                            arrowprops= \
                                dict(shrink=0.05, width=0.1, headwidth = 0.1))
        
        ax1[0].axis([0, self.tsim, -0.001, 0.75])
        
        # remove y axis and spines
        ax1[0].get_yaxis().set_visible(False)
        ax1[0].get_xaxis().set_visible(False)
        for spine in ["left", "top", "right","bottom"]:
            ax1[0].spines[spine].set_visible(False)
        
        
        # Plot power in - power out
        ax1[1].plot(self.sim_data["t"], self.sim_data["p_in"], 'black', \
                    self.sim_data["t"], self.sim_data["p_out"],'red')
        ax1[1].set_xlim(0, self.tsim)
        ax1[1].set_xlabel('Time')
        ax1[1].set_ylabel('P_in and P_out [mW]')
        ax1[1].grid(True)
        
        
        # Plot battery charge
        battery_perc = []
        for entry in self.sim_data["battery"]:
            battery_perc.append(100*entry/self.batt_cap)
        ax1[2].plot(self.sim_data["t"], battery_perc, 'black')
        ax1[2].set_xlim(0, self.tsim)
        ax1[2].set_ylim(0, 100)
        ax1[2].set_xlabel('Time')
        ax1[2].set_ylabel('Battery %')
        ax1[2].grid(True)
        
        # Plot colour overlays
        if show_ops == 1:
            for q in range(len(ax1)):
                # collection = collections.BrokenBarHCollection.span_where(
                #     np.array(output_t), ymin=-1e10, ymax=1e10, where=np.array(output_sun) < 1, facecolor='black', alpha=0.6)
                # ax1[q].add_collection(collection)
                
                for os in list(self.opstates.keys()):
                    collection = collections.BrokenBarHCollection.span_where(
                        np.array(self.sim_data["t"]), \
                        ymin=-1e10, ymax=1e10, \
                        where=np.array(self.sim_data["OpState"]) == os, \
                        facecolor=opstate_colours[os], \
                        alpha=0.3)
                    ax1[q].add_collection(collection)
                    
        else:
            # Plot sunlight blocks
            for q in range(1,len(ax1)):
                collection = collections.BrokenBarHCollection.span_where(
                    np.array(self.sim_data["t"]), \
                    ymin=-1e10, \
                    ymax=1e10, \
                    where=np.array(self.sim_data["sun"]) == 1, \
                    facecolor='yellow', \
                    alpha=0.3)
                ax1[q].add_collection(collection)
                
                collection = collections.BrokenBarHCollection.span_where(
                    np.array(self.sim_data["t"]), \
                    ymin=-1e10, \
                    ymax=1e10, \
                    where=np.array(self.sim_data["sun"]) < 1, \
                    facecolor='black', \
                    alpha=0.6)
                ax1[q].add_collection(collection)
        
        
        fig1.tight_layout()
        
        # names = list(Pout_cum_ops.keys())
        # values = list(Pout_cum_ops.values())
        
        # fig1, ax2 = plt.subplots(1,2,figsize=(20, 7))
        
        # ax2[0].bar(ops_list, t_rel_ops , color=[ops_colours[i] for i in ops_colours], edgecolor='black', linewidth=1)
        # ax2[0].set_ylabel('Time %')
        # ax2[0].set_title('Relative operation duration over mission')
        
        # ax2[1].bar(ops_list, Pout_rel_ops , color=[ops_colours[i] for i in ops_colours], edgecolor='black', linewidth=1)
        # ax2[1].set_ylabel('Power use %')
        # ax2[1].set_title('Cumulative power consumption over mission')
        
        plt.show()
        
        
    def plot_pie_opstate(self, opstate_colours):
        
        if not self.schedule:
            raise RuntimeError("Plot cannot be made before a simulation is \
                               completed! Please run the .propagate() method \
                               before continuing!")
                               
        opstates = list(self.opstates.keys())
        
        opstate_perc = []
        for opstate in opstates:
            os_count = self.sim_data["OpState"].tolist().count(opstate)
            opstate_perc.append(100*os_count/len(self.sim_data["OpState"]))
        
        # Do plot
        fig1, ax1 = plt.subplots()
        ax1.pie(opstate_perc, labels=opstates, autopct='%1.1f%%',
                startangle=90)
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        ax1.set_title('Fraction of operational state over whole mission')
        
        plt.show()
