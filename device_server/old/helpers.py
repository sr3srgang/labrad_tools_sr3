import importlib

from exceptions import DeviceImportError


def import_device_class(device_name):
    try:
        module_path = 'labrad_devices.{}'.format(device_name)
        module = importlib.import_module(module_path)
        reload(module)
        return module.__device__
    except:
        raise DeviceImportError(device_name)

