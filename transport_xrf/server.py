#!/usr/bin/python3

from labrad.server import setting #, LabradServer
from device_server.server import DeviceServer
import json
import jsonplus
# from twisted.internet import defer, reactor

from mogdevice_custom import MOGDevice
import time
import os
import sys
import traceback
import datetime


LATTICE_WAVELENGTH = 813.428e-9 # m
LATTICE_CONSTANT = LATTICE_WAVELENGTH/2 # m
BASE_FREQUENCY= 111.2e6 # Hz
AMPLITUDE = -17.70 # dBm
DDS_FREQ_STEP = 0.232831 # Hz
FM_GAIN_BIT = 15

class TransportXRFServer(DeviceServer):
    # name as a Labrad server
    # Also, name in the DeviceServer.devices static dictionary (via DeviceServer._initialize_devices())
    name = 'transport_xrf_device_server'
 
    # print useful debug messages if enabled
    DEBUG_MODE = True
    def print_debug(self, str):
        if self.DEBUG_MODE is not True:
            return
        print("[DEBUG] " + str + "\n\tfrom " + __file__)
    
    

    def __init__(self):
        # essentially inherited LabradServers's __init__ method; no need to modify it.
        # In particular, the object already has Labrad client `self.cxn` defined.
        super(TransportXRFServer, self).__init__()
        print(">>>>>>> trasport_xrf device server >>>>>>>")
    
    def initServer(self):
        """overidding initServer() placeholder in LabradServer"""
        
        # load template table scripts for legacy transport
        script_dir = os.path.dirname(__file__)
        self.script_dir = script_dir
        template_path = os.path.join(script_dir, "TPA_header_template.txt")
        with open(template_path, "r") as file:
            header_template_script = file.read()
        self.header_template_script = header_template_script

        template_path = os.path.join(script_dir, "TPA_transport_template.txt")
        with open(template_path, "r") as file:
            transport_template_script = file.read()
        self.transport_template_script = transport_template_script
   
        template_path = os.path.join(script_dir, "TPA_footer_template.txt")
        with open(template_path, "r") as file:
            footer_template_script = file.read()
        self.footer_template_script = footer_template_script
        print("Legacy tranport templates loaded.")
        
        # connect to Moglabs XRF
        device_address = '192.168.1.190'
        print("Connecting to device...", end=" ")
        try:
            dev = MOGDevice(device_address)
        except Exception as ex:
            # attempt close connection and raise the error
            try:
                dev.close()
            except:
                pass
            raise ex

        self.dev = dev
        print("Done.")
        # Print device info for confirmation
        print("\tDevice info:", dev.ask('info'))

    def stopServer(self):
        """overidding stopServer() placeholder in LabradServer"""
        # close the Mogslab XRF connection
        print("Disconnecting from the device...", end=" ")
        self.dev.close()
        print("Done.")
  
             
    def generate_transport_entries(self, x, d):
        phin = x/LATTICE_CONSTANT
        df = 3*phin/2/d
        t_ramp = t_hold = d / 3
        ramp_step_num = 10000 # TBD
        t_ramp_step = t_ramp / ramp_step_num
        freq_to_ramp = BASE_FREQUENCY + df
        
        return self.transport_template_script.format(
            base_freq=f"{BASE_FREQUENCY/1e6}MHz",
            freq_to_ramp=f"{freq_to_ramp/1e6}MHz",
            t_ramp_step=f"{t_ramp_step*1e6}us",
            ramp_step_num=f"{ramp_step_num}",
            t_hold=f"{t_hold*1e6}us",
        )
        
   
    def generate_legacy_transport(self, request):
        x_long = request["x_long"]
        d_long = request["d_long"]
        x_short = request["x_short"]
        d_short = request["d_short"]
        up_down_sequence_short = request["up_down_sequence_short"]
        
        msg_debug = ( 
                     "Got transport parameters:\n"
                     f"\n\tlong: x={x_long}, d={d_long}"
                     f"\n\tshort: x={x_short }, d={d_short}"
        )
        self.print_debug(msg_debug)
        
        # variable to store the script to send to Moglabs XRF
        script = ""

        # load & format templates
        # # header
        script += self.header_template_script.format(base_freq=f"{BASE_FREQUENCY/1e6}MHz", amp=f"{AMPLITUDE}dBm")

        # # transports
            
        # # # long transport up
        script += "; LONG TRASPORT UP\n\n"
        script += "TABLE,XPARAM,1,FREQ,8\n" # step resolution = 59.6 Hz
        script += self.generate_transport_entries(x_long, d_long)

        # # short transports
        if up_down_sequence_short:
            script += "; SHORT TRASPORTS\n\n"
            script += "TABLE,XPARAM,1,FREQ,5\n" # step resolution = 7.45 Hz
            for multiplier in up_down_sequence_short:
                script += "; up\n" if multiplier == +1 else "; down\n"
                x = multiplier*x_short
                script += self.generate_transport_entries(x, d_short)

        # # footer
        script += self.footer_template_script.format(base_freq=f"{BASE_FREQUENCY/1e6}MHz")
        
        if self.DEBUG_MODE:
            save_path = os.path.join(self.script_dir, "DEBUG_legacy_table_script.txt")
            self.print_debug(f"Saving generated script to {save_path} ...")
            with open(save_path, "w") as file:
                file.write(script)
            self.print_debug("Saved.")
            
        return script

     
     
    # Caution: setting number has to start from 10. 0 -- 9 are reserved for DeviceServer.     
 
    @setting(10)
    def update(self, c, request_jsonplus = '{}'): # use jsonplus instead of json to preserve tuple type in transport sequence
        self.print_debug('transport_xrf_device_server.update() called.')
        start = time.time()
        try:
            request = jsonplus.loads(request_jsonplus) # got transport_sequence from `transport_xrf.small_table_script_generator`` conductor parameter.        re
            # 813.428
            is_legacy_transport = request["is_legacy_transport"]
            if is_legacy_transport:
                # generate table script for legacy transport
                script = self.generate_legacy_transport(request)
                # send script to Moglabs XRF
                commands, responses = self.dev.send_script(script)
                print("Sent script to Moglabs XRF.")
                if self.DEBUG_MODE:
                    msg = ">>>>>> Communication with Moglabs XRF  >>>>>\n"
                    for ic in range(len(commands)):
                        msg += ( f"Command: {commands[ic]}\n"
                                f"\tResponse: {responses[ic]}\n"
                        )
                    msg += "<<<<< Communication with Moglabs XRF  <<<<<\n"
                    
                    save_path = os.path.join(self.script_dir, "DEBUG_xrf_commands_responses.txt")
                    self.print_debug(f"Saving generated script to {save_path} ...")
                    with open(save_path, "w") as file:
                        file.write(msg)
                return
   
            raise NotImplementedError("Non-legacy transports comming soon...")
    #        transport_sequence = request['transport_sequence']
    #         self.print_debug('Got transport sequence: {}'.format(transport_sequence))

               
        except:
            print("Some error in transport_xrf server.")
            print("Some error in transport_xrf server.", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
        finally:
            end = time.time()
            print(f"Time elapsed for preparing transport_xrf = {end - start} s.")
        
    
Server = TransportXRFServer

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())

    #Server.initialize_devices(json.dumps({'cavity_pico': {}}))
    #print('test')
    
    print("<<<<<<< trasport_xrf device server <<<<<<<")