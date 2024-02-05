#from current_controller.devices._3d import DeviceProxy as _3DProxy
#from current_controller.devices._2d import DeviceProxy as _2DProxy
#from current_controller.devices.zs import DeviceProxy as ZSProxy
#from current_controller.devices._3d2 import DeviceProxy as _3D2Proxy
from current_controller.devices._mot import DeviceProxy as _motProxy
from current_controller.devices._zeeman import DeviceProxy as _zeemanProxy
from current_controller.clients.default import CurrentControllerClient
from current_controller.clients.default import MultipleClientContainer

'''
class _3DClient(CurrentControllerClient):
    DeviceProxy = _3DProxy
    name = '3d'

class _2DClient(CurrentControllerClient):
    DeviceProxy = _2DProxy
    name = '2d'

class ZSClient(CurrentControllerClient):
    DeviceProxy = ZSProxy
    name = 'zs'

class _3D2Client(CurrentControllerClient):
    DeviceProxy = _3D2Proxy
    name = '3d2'
'''
class _zeemanClient(CurrentControllerClient):
    DeviceProxy = _zeemanProxy
    name = 'Zeeman'
    
class _motClient(CurrentControllerClient):
    DeviceProxy = _motProxy
    name = 'MOT'
    


class MyClientContainer(MultipleClientContainer):
    name = 'blue injection lasers'

if __name__ == '__main__':
    from PyQt4 import QtGui
    app = QtGui.QApplication([])
    app.setWindowIcon(QtGui.QIcon('icon_image_blueLaser.png'))
    from client_tools import qt4reactor 
    qt4reactor.install()
    from twisted.internet import reactor

    widgets = [_motClient(reactor), _zeemanClient(reactor)]#(reactor)]#_3DClient(reactor), _2DClient(reactor), ZSClient(reactor), _3D2Client(reactor)]
    widget = MyClientContainer(widgets, reactor)
    widget.show()
    reactor.run()
