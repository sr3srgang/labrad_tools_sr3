from server_tools.threaded_server import ThreadedServer
from labrad.server import setting

from hardware_interface_server.exceptions import InterfaceNotAvailable

class HardwareInterfaceServer(ThreadedServer):
    """ template for hardware interface server """
    interfaces = {}

    def initServer(self):
        available_interfaces = self._get_available_interfaces()
        print "available interfaces on {}:".format(self.name)
        for interface_id in available_interfaces:
            print "\t{}".format(interface_id)

    def stopServer(self):
        close_config = {interface_id: {} for interface_id 
                in self.interfaces}
        self._close_interface(close_config)

    def _get_interface(self, interface_id):
        open_interfaces = self._get_open_interfaces()
        if interface_id not in open_interfaces:
            self._open_interface(interface_id)
        return self.interfaces[interface_id]

    @setting(0)
    def get_available_interfaces(self, c):
        """ Get list of available interfaces """
        available_interfaces = self._get_available_interfaces()
        return available_interfaces

    def _get_available_interfaces(self):
        """ to be implemented by children """
        return []
    
    @setting(1)
    def get_open_interfaces(self, c):
        """ Get list of interfaces with open connections """
        open_interfaces = self._get_open_interfaces()
        return open_interfaces

    def _get_open_interfaces(self):
        """ to be implemented by children """
        return []
    
    @setting(2)
    def open_interface(self, c, interface_id):
        """"""
        self._open_interface(interface_id)

    def _open_interface(self, interface_id):
        """ to be implemented by children """
        return None
    
    @setting(3)
    def close_interface(self, c, interface_id):
        self._close_interface(interface_id)

    def _close_interface(self, interface_id):
        """ to be implemented by children """
        return None
    
    @setting(4)
    def reopen_interface(self, c, interface_id):
        self._reopen_interface(interface_id)
    
    def _reopen_interface(self, interface_id):
        try:
            self._close_interface(interface_id)
        except InterfaceNotAvailable:
            pass
        self._open_interface(interface_id)
