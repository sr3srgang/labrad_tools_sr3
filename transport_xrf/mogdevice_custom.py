# 2025/03/07: Created by Joonseok Hur
# A wrapper for mogdevice.MOGDevice class to
# add more methods: send_script and send_file
# (see docstrings of the methods for details)

from mogdevice import MOGDevice as BaseMOGDevice

class MOGDevice(BaseMOGDevice):
    """
    Extended MOGDevice with additional functionality to send table script commands.
    """
    def __new__(cls, address, isDummy=False):
        if isDummy:
            return MOGDevice_dummy(address)
        return super().__new__(cls)
    
    def __init__(self, address, isDummy=False):
        # Only initialize if not a dummy.
        if isDummy:
            return
        super().__init__(address)
        
    def send_script(self, script_text):
        """
        Sends the provided script string to the synthesizer.
        Each non-empty, non-comment line is sent as a command.

        :param script_text: A string containing the complete table script.
        """
        print("Sending script to device:")
        # print(script_text)
        commands = script_text.strip().splitlines()
        responses = [None]*len(commands)
        for ic, line in enumerate(commands):
            command = line.strip()
            if not command or command.startswith(';'):
                continue  # Skip empty lines and comments
            response = self.cmd(command)
            responses[ic] = response
            # print("Command:", command, "\n\tResponse:", response)
        return commands, responses
        
        # Optionally dump the binary table to verify that it was programmed correctly.
        # binary_table = self.ask_bin('TABLE,DUMP,1')
        # print("Binary table length:", len(binary_table))

    def send_file(self, script_file_path):
        """
        Loads a table script from the given file path and sends it to the synthesizer.

        :param script_file_path: Path to the script file (e.g., "simple_sinusoidal_freq_ramp.atm")
        """
        try:
            with open(script_file_path, "r", encoding="utf-8") as f:
                script_text = f.read()
        except Exception as e:
            print(f"Error reading script file: {e}")
            return

        # print("Loaded script from", script_file_path)
        return self.send_script(script_text)


class MOGDevice_dummy(BaseMOGDevice):
    """
    Dummy MOGDevice class for testing
    """
    def __init__(self, address):
        self.address = address
        print("Dummy device initialized at", address)

    def ask(self, command):
        print("Dummy ask called with:", command)
        return "Dummy response"

    def cmd(self, command):
        print("Dummy cmd called with:", command)
        return "OK"

    def ask_dict(self, command):
        print("Dummy ask_dict called with:", command)
        return {"dummy_key": "dummy_value"}

    def ask_bin(self, command):
        print("Dummy ask_bin called with:", command)
        return b"Dummy binary data"

    def close(self):
        print("Dummy device closed")


# Example usage:
if __name__ == '__main__':
    # For Ethernet connection, use the device IP (e.g., '10.1.1.23')
    # For USB connection, use the COM port (e.g., 'COM4')
    
    device_address = '192.168.1.190'
    print("Connecting to device...", end=" ")
    dev = MOGDevice(device_address)
    print("Done.")
    # Print device info for confirmation
    print("\tDevice info:", dev.ask('info'))
    print()

    # Program the device using a script string
    base_freq = 110e6  # Hz; 110 MHz
    power = 7.5  # 30 dBm
    template_script = \
"""
MODE,1,NSB
FREQ,1,{base_freq}Hz
POW,1,{power}dBm
ON,1
"""
    script = template_script.format(base_freq=base_freq,power=power)  # Example frequency

    print("Sending script:")
    print(script)
    print()
    
    commands, responses = dev.send_script(script)
    
    print("Script sent:")
    for ic in range(len(commands)):
        print("Command:", commands[ic])
        print("\tResponse:", responses[ic])
    print()
    
    # # Program the device using the script file
    # script_file = "simple_sinusoidal_freq_ramp.atm"
    # dev.send_file(script_file)

    # Close the device connection when done
    dev.close()

