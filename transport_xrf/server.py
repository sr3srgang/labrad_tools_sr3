#!/usr/bin/python3

from labrad.server import setting #, LabradServer
from device_server.server import DeviceServer
import json
import jsonplus
# from twisted.internet import defer, reactor

from mogdevice_custom import MOGDevice
from transport_xrf.constants import *
from legacy_transport.legacy_transport import LegacyTransport

import time
import os
import sys
import traceback
import datetime
from pathlib import Path


LATTICE_WAVELENGTH = 813.428e-9 # m
LATTICE_CONSTANT = LATTICE_WAVELENGTH/2 # m
BASE_FREQUENCY= 111.2e6 # Hz
AMPLITUDE = -17.70 # dBm
DDS_FREQ_STEP = 0.232831 # Hz
TPA_FREQ_GAIN_BIT = 15

class TransportXRFServer(DeviceServer):
    # name as a Labrad server
    # Also, name in the DeviceServer.devices static dictionary (via DeviceServer._initialize_devices())
    name = 'transport_xrf_device_server'
 
    # print useful debug messages if enabled
    DEBUG_MODE = False
    def print_debug(self, str):
        if self.DEBUG_MODE is not True:
            return
        print("[DEBUG] " + str + "\n\tfrom " + __file__)
        
    SCRIPT_DIR = Path(__file__).resolve().parent
    
    # >>>>>>> LabradServer methods >>>>>>>

    def __init__(self):
        # essentially inherited LabradServers's __init__ method; no need to modify it.
        # In particular, the object already has Labrad client `self.cxn` defined.
        super(TransportXRFServer, self).__init__()
    
    def initServer(self):
        """overidding initServer() placeholder in LabradServer"""
        
        # connect to Moglabs XRF
        device_address = '192.168.1.190'
        print("Connecting to device...", end=" ")
        try:
            dev = MOGDevice(device_address)
        except Exception as ex:
            # attempt close connection and raise the error
            try: dev.close()
            except: pass
            finally: raise ex

        self.dev = dev
        print("Done.")
        # Print device info for confirmation
        print("\tDevice info:", dev.ask('info'))
        
        # instantiate legacy transport class
        self.legacy_transport = LegacyTransport()
        

    def stopServer(self):
        """overidding stopServer() placeholder in LabradServer"""
        # close the Mogslab XRF connection
        print("Disconnecting from the device...", end=" ")
        self.dev.close()
        print("Done.")
        
    # <<<<<<< LabradServer methods <<<<<<<
  


    # >>>>>>> trasport methods >>>>>>>
    
    def _send_script(self, script):
        commands, responses = self.dev.send_script(script)
        self.print_debug("Sent script to Moglabs XRF.")
        
        if self.DEBUG_MODE:
            msg = ">>>>>> Communication with Moglabs XRF  >>>>>\n"
            for ic in range(len(commands)):
                msg += ( f"Command: {commands[ic]}\n"
                        f"\tResponse: {responses[ic]}\n"
                )
            msg += "<<<<< Communication with Moglabs XRF  <<<<<\n"
            
            save_path = self.SCRIPT_DIR / "DEBUG_xrf_commands_responses.txt"
            self.print_debug(f"Saving generated script to {save_path} ...")
            with open(save_path, "w") as file:
                file.write(msg)

    # Caution: setting number has to start from 10. 0 -- 9 are reserved for DeviceServer.      
    @setting(10)
    def update_transport(self, c, request_jsonplus = '{}'): # use jsonplus instead of json to preserve tuple type in transport sequence
        self.print_debug('transport_xrf_device_server.update() called.')
        start = time.time()
        try:
            # >>>>> Get advanced table script for transport to send to Moglab XRF >>>>>
            request = jsonplus.loads(request_jsonplus) # got transport_sequence from `transport_xrf.small_table_script_generator`` conductor parameter.        re
            # 813.428
            is_legacy_transport = request["is_legacy_transport"]
            if is_legacy_transport:
                # generate table script for legacy transport
                script, Af, freq_gain, t_ramp_step, ramp_step_num = self.legacy_transport._get_transport_script(request)
                
                msg = f"Legacy mode. Af={Af}, freq_gain={freq_gain}, t_ramp_step={t_ramp_step}, ramp_step_num={ramp_step_num}"
            else:
            # raise NotImplementedError("Non-legacy transports comming soon...")
                transport_sequence = request['transport_sequence']
                self.print_debug('Got transport sequence: {}'.format(transport_sequence))
                
            # <<<<< Get advanced table script for transport to send to Moglab XRF <<<<<
            
            # >>>>> send script to Moglabs XRF >>>>>
            
            self._send_script(script)
            print('Trasport updated: ' + msg)
            
            # <<<<< send script to Moglabs XRF <<<<<
             
             
            # >>>>> Upload to InfluxDB >>>>>         

            # uploader_server_name = "influxdb_uploader_server"
            # uploader_server = getattr(self.cxn, uploader_server_name, None)
            # if uploader_server is None:
            #     print(f"`{uploader_server_name}` server not found.")
            #     print(traceback.format_exc(), file=sys.stderr)
            # else:
            #     methodname = "upload_experiment_shot"
            #     upload_experiment_shot = getattr(uploader_server, methodname, None)
            #     if upload_experiment_shot is None:
            #         print("No upload_experiment_shot")
            #     upload_experiment_shot(self, c, exp_rel_path, shot_num, timestamp, uploaded_from,
            #        fields_json, tags_json, measurement):
            #     try:
            #         uploader_server.upload_conductor_parameters(
            #             exp_rel_path=request["exp_rel_path"],
            #             shot_num=request["shot_num"],
            #             parameters_json=json.dumps(request),
            #         )
            #     except:
            #         print("Failed to upload data to InfluxDB.")
            #         print(traceback.format_exc(), file=sys.stderr)
            
            # <<<<< Upload to InfluxDB <<<<<  
            
        except:
            print("Some error in transport_xrf server.")
            print("Some error in transport_xrf server.", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
        finally:
            end = time.time()
            self.print_debug(f"Time elapsed for preparing transport_xrf = {end - start} s.")
            
    # <<<<<<< trasport methods <<<<<<<
        
    
Server = TransportXRFServer

if __name__ == "__main__":
    from labrad import util
    print(">>>>>>> trasport_xrf device server >>>>>>>")
    util.runServer(Server())
    print("<<<<<<< trasport_xrf device server <<<<<<<")