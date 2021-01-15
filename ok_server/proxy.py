class OKProxy(object):
    def __init__(self, ok_server):
        self.ok_server = ok_server

    def okCFrontPanel(self):
        fp = okCFrontPanelProxy(self.ok_server)
        return fp

class okCFrontPanelProxy(object):
    def __init__(self, ok_server):
        self.ok_server = ok_server

    def OpenBySerial(self, interface_id):
        self.ok_server.reopen_interface(interface_id)
        self.interface_id = interface_id

    def ConfigureFPGA(self, filepath):
        return self.ok_server.configure_fpga(self.interface_id, filepath)

    def GetWireOutValue(self, address):
        return self.ok_server.get_wire_out_value(self.interface_id, address)

    def IsTriggered(self, address):
        return self.ok_server.is_triggered(self.interface_id, address)

    def SetWireInValue(self, address, value):
        return self.ok_server.set_wire_in_value(self.interface_id, address, value)

    def UpdateTriggerOuts(self):
        return self.ok_server.update_trigger_outs(self.interface_id)

    def UpdateWireIns(self):
        return self.ok_server.update_wire_ins(self.interface_id)
    
    def UpdateWireOuts(self):
        return self.ok_server.update_wire_outs(self.interface_id)

    def WriteToPipeIn(self, address, byte_array):
        return self.ok_server.write_to_pipe_in(self.interface_id, address, byte_array)

    def _wait_trigger(self, address):
        return self.ok_server.wait_trigger(self.interface_id, address)
