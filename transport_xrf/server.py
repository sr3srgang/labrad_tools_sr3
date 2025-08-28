#!/usr/bin/python3

from labrad.server import setting #, LabradServer
from device_server.server import DeviceServer
import json
import jsonplus
# from twisted.internet import defer, reactor

from mogdevice_custom import MOGDevice
from transport_xrf.constants import *
from transport.transport import Transport
from legacy_transport.legacy_transport import LegacyTransport

import time
import os
import sys
import traceback
import datetime
from pathlib import Path


class TransportXRFServer(DeviceServer):
    # name as a Labrad server
    # Also, name in the DeviceServer.devices static dictionary (via DeviceServer._initialize_devices())
    name = 'transport_xrf_device_server'
 
    # print useful debug messages if enabled
    DEBUG_MODE = False
    # DEBUG_MODE = True
    def print_debug(self, str):
        if self.DEBUG_MODE is not True:
            return
        print("[DEBUG] " + str + "\n\tfrom " + __file__)
        
    SCRIPT_DIR = Path(__file__).resolve().parent / "table scripts"
    
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
        dev = None
        try:
            dev = MOGDevice(device_address)
            # dev = MOGDevice(device_address, isDummy=True) # init dummy device for debug
        except Exception as ex:
            # attempt close connection and raise the error
            try: 
                if dev is not None: dev.close()
            except: pass
            finally: raise ex

        self.dev = dev
        print("Done.")
        # Print device info for confirmation
        print("\tDevice info:", dev.ask('info'))
        
        # instantiate legacy transport class
        self.transport = Transport()
        self.legacy_transport = LegacyTransport()
        

    def stopServer(self):
        """overidding stopServer() placeholder in LabradServer"""
        # close the Mogslab XRF connection
        print("Disconnecting from the device...", end=" ")
        self.dev.close()
        print("Done.")
        
    # <<<<<<< LabradServer methods <<<<<<<

    # >>>>>>> trasport methods >>>>>>>
    
    # def get_transport_script(self, request):
    #     # raise NotImplementedError("Non-legacy transports comming soon...")
    #     # transport_sequence = request['transport_sequence']
    #     # self.print_debug('Got transport sequence: {}'.format(transport_sequence))
        
    #     freq_gain = request["freq_gain"]
    #     d_long = request["d_long"]
    #     t_long = request["t_long"]
    #     d_short = request["d_short"]
    #     t_short = request["t_short"]
    #     up_down_sequence_short = request["up_down_sequence_short"]
    #     print("SEQUENCE", up_down_sequence_short)

    #     script = ""
    
    def _send_script(self, script):
        """
        Send script to Moglabs (and save the generated table script in debug mode).
        """
        # commands, responses = self.dev.send_script(script, send_batch=True, get_response=False)
        commands, responses = self.dev.send_script(script, send_batch=False, get_response=True)
        self.print_debug("Sent script to Moglabs XRF.")
        
        if self.DEBUG_MODE:
            msg = ">>>>>> Communication with Moglabs XRF  >>>>>\n"
            for ic in range(len(commands)):
                msg += ( f"Command: {commands[ic]}\n"
                        f"\tResponse: {responses[ic]}\n"
                )
            msg += "<<<<< Communication with Moglabs XRF  <<<<<\n"
            self.print_debug(msg)
                
        save_path = self.SCRIPT_DIR / "table_script_sent.txt"
        print(f"Saving generated script to {save_path} ...", end=" ")
        with open(save_path, "w") as file:
            file.write(script)
        print("Done.")
        
    # def upload_to_influxdb(self, request):
    #     uploader_server_name = "influxdb_uploader_server"
    #     uploader_server = getattr(self.cxn, uploader_server_name, None)
    #     if uploader_server is None:
    #         print(f"`{uploader_server_name}` server not found.")
    #         print(traceback.format_exc(), file=sys.stderr)
    #     else:
    #         methodname = "upload_experiment_shot"
    #         upload_experiment_shot = getattr(uploader_server, methodname, None)
    #         if upload_experiment_shot is None:
    #             print("No upload_experiment_shot")
    #         upload_experiment_shot(self, c, exp_rel_path, shot_num, timestamp, uploaded_from,
    #             fields_json, tags_json, measurement)
    #         try:
    #             uploader_server.upload_conductor_parameters(
    #                 exp_rel_path=request["exp_rel_path"],
    #                 shot_num=request["shot_num"],
    #                 parameters_json=json.dumps(request),
    #             )
    #         except:
    #             print("Failed to upload data to InfluxDB.")
    #             print(traceback.format_exc(), file=sys.stderr)

    # Caution: setting number has to start from 10. 0 -- 9 are reserved for DeviceServer.      
    @setting(10)
    def update_transport(self, c, request_jsonplus = '{}'): # use jsonplus instead of json to preserve tuple type in transport sequence
        self.print_debug('transport_xrf_device_server.update() called.')
        t_start = time.time()
        try:
            # >>>>> Get advanced table script for transport to send to Moglab XRF >>>>>
            
            request = jsonplus.loads(request_jsonplus) # got transport_sequence from `transport_xrf.small_table_script_generator`` conductor parameter.        re
            # 813.428
            is_legacy_transport = request["is_legacy_transport"]
            if is_legacy_transport:
                # generate table script for legacy transport
                script, freq_gain, Af, t_ramp_step, ramp_step_num = self.legacy_transport.get_transport_script(request)
                # print(script)
                msg = f"Legacy mode. freq_gain={freq_gain}, Af={Af}, t_ramp_step={t_ramp_step}, ramp_step_num={ramp_step_num}"
            else:
                msg = ""
                is_there_short = bool(request["up_down_sequence_short"])
                script, metadata = self.transport.get_transport_script(request)
                msg += "\n\tlong transport: "
                if request["form_long"] == "legacy":
                    msg += "legacy form"
                else:
                    msg += f"distance error={metadata['long_up']['transport_error']*100:.3f}%"
                if is_there_short:
                    msg += "\n\tshort transport: "
                    if request["form_short"] == "legacy":
                        msg += "legacy form"
                    else:
                        msg += f"distance error={metadata['short_up']['transport_error']*100:.3f}% (up), {metadata['short_down']['transport_error']*100:.3f}% (down)"

            # <<<<< Get advanced table script for transport to send to Moglab XRF <<<<<
            
            
            # >>>>> send script to Moglabs XRF >>>>>
            start_send = time.time()
            self._send_script(script)
            end_send = time.time(); t_exe_send = end_send - start_send
            print('Trasport updated: ' + msg)
            print()
            
            # <<<<< send script to Moglabs XRF <<<<<
             
             
            # upload to InfluxDB
            # self.upload_to_influxdb(request)     


        except:
            print("Some error in transport_xrf server.")
            print("Some error in transport_xrf server.", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
        finally:
            t_end = time.time(); t_exe = t_end - t_start
            # self.print_debug(f"Time elapsed for preparing transport_xrf = {end - start} s.")
            print(f"Time elapsed for preparing transport_xrf = {t_exe} s.")
            print(f"\t- {t_exe_send} s to send script to Moglabs XRF.")

    # <<<<<<< trasport methods <<<<<<<
        
    
Server = TransportXRFServer

if __name__ == "__main__":
    from labrad import util
    print(">>>>>>> trasport_xrf device server >>>>>>>")
    util.runServer(Server())
    print("<<<<<<< trasport_xrf device server <<<<<<<")