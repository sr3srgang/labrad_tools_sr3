"""
### BEGIN NODE INFO
[info]
name = ok
version = 1.0
description = 
instancename = %LABRADNODE%_ok

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

import json
import os
import time

from labrad.server import setting

import ok

from hardware_interface_server.server import HardwareInterfaceServer
from hardware_interface_server.exceptions import InterfaceAlreadyOpen
from hardware_interface_server.exceptions import InterfaceNotAvailable
from ok_server.exceptions import BitfileNotFound

class OKServer(HardwareInterfaceServer):
    name = '%LABRADNODE%_ok'
    bitfile_directory = os.path.join(os.getenv('PROJECT_LABRAD_TOOLS_PATH'), 'ok_server', 'bit')
    
    def _get_available_interfaces(self):
        open = self._get_open_interfaces()
        available_but_not_open = []
        
        fp = ok.okCFrontPanel()
        device_count = fp.GetDeviceCount()
        for i in range(device_count):
            serial_number = fp.GetDeviceListSerial(i)
            available_but_not_open.append(serial_number)
        
        return open + available_but_not_open

    def _get_open_interfaces(self):
        for interface_id, interface in self.interfaces.items():
            try: 
                is_open = interface.IsOpen()
                if not is_open:
                    del self.interfaces[interface_id]
            except:
                del self.interfaces[interface_id]

        return self.interfaces.keys()
        
    def _open_interface(self, interface_id):
        open = self._get_open_interfaces()
        if interface_id in open:
            raise InterfaceAlreadyOpen(interface_id)

        fp = ok.FrontPanel()
        error = fp.OpenBySerial(interface_id)
        if error:
            raise InterfaceNotAvailable(interface_id)
        fp.LoadDefaultPLLConfiguration()
        self.interfaces[interface_id] = fp

    def _close_interface(self, interface_id):
        interface = self._get_interface(interface_id)
        interface.Close()
        del self.interfaces[interface_id]

    @setting(10)
    def configure_fpga(self, c, interface_id, file_name):
        interface = self._get_interface(interface_id)
        file_path = os.path.join(self.bitfile_directory, file_name)
        if not os.path.isfile(file_path):
            raise BitfileNotFound(file_name)
        interface.ConfigureFPGA(file_path)
    
    @setting(11)
    def get_wire_out_value(self, c, interface_id, wire_address):
        interface = self._get_interface(interface_id)
        wire_out_value = interface.GetWireOutValue(wire_address)
        return wire_out_value
    
    @setting(12)
    def is_triggered(self, c, interface_id, address, mask=0xffffffff):
        interface = self._get_interface(interface_id)
        is_triggered = interface.IsTriggered(address, mask)
        return bool(is_triggered)
    
    @setting(13)
    def set_wire_in_value(self, c, interface_id, wire_address, value):
        interface = self._get_interface(interface_id)
        interface.SetWireInValue(wire_address, value)
    
    @setting(14)
    def update_trigger_outs(self, c, interface_id):
        interface = self._get_interface(interface_id)
        interface.UpdateTriggerOuts()
    
    @setting(15)
    def update_wire_ins(self, c, interface_id):
        interface = self._get_interface(interface_id)
        interface.UpdateWireIns()
    
    @setting(16)
    def update_wire_outs(self, c, interface_id):
        interface = self._get_interface(interface_id)
        interface.UpdateWireOuts()
    
    @setting(17, interface_id='s', pipe_address='i', byte_array='*y')
    def write_to_pipe_in(self, c, interface_id, pipe_address, byte_array):
        interface = self._get_interface(interface_id)
        interface.WriteToPipeIn(pipe_address, bytearray(byte_array))

    @setting(101)
    def wait_trigger(self, c, interface_id, address, mask=0xffffffff):
        interface = self._get_interface(interface_id)
        interface.UpdateTriggerOuts()
        is_triggered = interface.IsTriggered(address, mask)
        while True:
            interface.UpdateTriggerOuts()
            is_triggered = interface.IsTriggered(address, mask)
            if is_triggered:
                return
            time.sleep(0.005)

Server = OKServer

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())
