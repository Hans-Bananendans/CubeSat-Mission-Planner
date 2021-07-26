class OpState:
    """This class represents a separate operational state, and can be used
    to calculate used power values and separate these by channel."""
    
    def __init__(self, device_power_values, channels, device_channels, \
                 blips_on=1):
        
        self.device_power_values = device_power_values
        self.devices = list(device_power_values.keys())
        self.channels = channels
        self.device_channels = device_channels
        
        self.blips_on = blips_on
        
    def power_used_channel(self):
        
        # Generate empty dictionary
        channel_power = {chan: 0 for chan in self.channels}
        
        # Calculate power for each channel
        for device in self.devices:
            # Find which power channel the device is connected to
            chan = self.device_channels[device]
            # Add power used by the device to total power used by channel
            channel_power[chan] += self.device_power_values[device]
        
        return channel_power
    
    def power_used_device(self):
        return self.device_power_values
    
    def power_used(self):
        return sum(self.device_power_values.values())
    
    def blips(self):
        return self.blips_on