# From https://github.com/sr3srgang/20250307-Moglabs-XRF-synthesizer----ramp-with-table-mode/blob/56c07de340274dc13d17198e3e5aebb0f69e6d93/mogdevice_custom/mogdevice_custom.py

# 2025/03/07: Created by Joonseok Hur
# 2025/08/19: last modified by JH
# A wrapper for mogdevice.MOGDevice class to
# add more methods: send_script and send_file
# (see docstrings of the methods for details)

from mogdevice import MOGDevice as BaseMOGDevice
import time

CRLF = b"\r\n"

class MOGDevice(BaseMOGDevice):
    MAX_TABLE_ENTRY_NUM = 8191
    
    def __new__(cls, address, isDummy=False):
        if isDummy:
            return MOGDevice_dummy(address)
        return super().__new__(cls)
    
    def __init__(self, address, isDummy=False):
        # Only initialize if this is a true MOGDevice instance.
        if type(self) is not MOGDevice:
            # Already initialized as a dummy.
            return
        super().__init__(address)
        # ... additional initialization for non-dummy instances
        
    def _get_command_batch(self, cmds):
        """
        Prepares a batch of commands for sending to the device.
        """
        # ensure each line ends with CRLF; add a final CRLF
        cmds = [cmd.rstrip("\r\n") for cmd in cmds] # strip CRLF if any;
        payload = "\r\n".join(cmds) + "\r\n"  # join lines with CRLF and add the CRLF at the end
        # payload = payload.encode() # encode to bytes
        return payload
    
    def send_batch(self, cmds):
        """
        Send a batch of commands to the device and returns the responses.
        Only use if each command produces a short single-line text reply or an exception will be raised.
        """
        # 1) Build one big payload (ensure each line ends with CRLF; add a final CRLF)
        payload = self._get_command_batch(cmds)
        payload = payload.encode() # encode to bytes

        # 2) Clear stale device output
        self.flush()

        # 3) Single write to device
        self.send_raw(payload)

    def cmd_batch(self, cmds):
        """
        Commands (send command & receive response) a batch of commands to the device and returns the responses.
        Only use if each command produces a short single-line text reply or an exception will be raised.
        """
        num_cmd = len(cmds)
        
        self.send_batch(cmds)

        # 4) Drain responses
        timeout = 1 # seconds
        deadline = time.time() + timeout
        buf = b""
        while not buf:
            buf = self.flush(timeout=0.1)
            if time.time() > deadline:
                raise TimeoutError(f"No replies received before timeout ({timeout} s).")

        # 5) check if the responses are Unicode strings
        try:
            text = buf if isinstance(buf, str) else buf.decode()
        except UnicodeDecodeError as ex:
            raise Exception("Some responses are not Unicode strings.") from ex
        # split and validate count
        resps = [line.strip() for line in text.splitlines() if line.strip()]

        # 6) Check for device errors
        errors = []
        for i, (cmd, line) in enumerate(zip(cmds, resps), start=1):
            if line.startswith("ERR:"):
                errors.append(f"[Line {i}] {line}  | cmd={cmd!r}")
        if errors:
            raise RuntimeError("Device reported errors:\n\t" + "\n\t".join(errors))
        
        if len(resps) != num_cmd:
            # raise TimeoutError(f"Got {len(resps)}/{num_cmd} replies. Ensure each line returns exactly one-line response.")
            msg = "Got {len(resps)}/{num_cmd} replies. Ensure each line returns exactly one-line response."
            print("[Warning]" + msg + "\n\tfrom " + __file__)
        return resps
        
    def send_script(self, script_text, send_batch=False, get_response=True):
        """
        Sends the provided script string to the synthesizer.
        Each non-empty, non-comment line is sent as a command.
        Returns the commands and responses.

        :param script_text: A string containing the complete table script.
        """
        # format & filter script lines
        lines = []
        for line in script_text.strip().splitlines():
            line = line.strip()
            if not line or line.startswith(';'): # filter out the comment lines (with ;)
                continue
            lines += [line]
        lines = [line for line in lines if line]  # drop empty lines
        
        # send command
        commands = lines
        responses = [None]*len(commands)
        if send_batch is True:
            if get_response is True:
                responses = self.cmd_batch(commands)
            else:
                self.send_batch(commands)
        else:
            for ic, command in enumerate(commands):
                if get_response is True:
                    response = self.cmd(command)
                    responses[ic] = response
                else:
                    self.send(command)
        
        return commands, responses
    

    def send_file(self, script_file_path, send_batch = False):
        """
        Loads a table script from the given file path and sends it to the synthesizer.

        :param script_file_path: Path to the script file (e.g., "./simple_sinusoidal_freq_ramp.atm")
        """
        try:
            with open(script_file_path, "r", encoding="utf-8") as f:
                script_text = f.read()
        except Exception as e:
            print(f"Error reading script file: {e}")
            return

        print("Loaded script from", script_file_path)
        self.send_script(script_text, send_batch)


class MOGDevice_dummy(MOGDevice):
    """
    Dummy MOGDevice class for testing
    """
    def __init__(self, address, isDummy=True):
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

