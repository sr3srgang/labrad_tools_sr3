import traceback

class DeviceImportFailed(Exception):
    def __init__(self, device_name):
        traceback.print_exc()
        super(DeviceImportFailed, self).__init__(device_name)

class DeviceNotActive(Exception):
    def __init__(self, device_name):
        traceback.print_exc()
        super(DeviceNotActive, self).__init__(device_name)

class DeviceAlreadyActive(Exception):
    def __init__(self, device_name):
        traceback.print_exc()
        super(DeviceAlreadyActive, self).__init__(device_name)

class DeviceInitializationFailed(Exception):
    def __init__(self, device_name):
        traceback.print_exc()
        super(DeviceInitializationFailed, self).__init__(device_name)

class DeviceTerminationFailed(Exception):
    def __init__(self, device_name):
        traceback.print_exc()
        super(DeviceTerminationFailed, self).__init__(device_name)

class DeviceReloadFailed(Exception):
    def __init__(self, device_name):
        traceback.print_exc()
        super(DeviceReloadFailed, self).__init__(device_name)

class DeviceGetInfoFailed(Exception):
    def __init__(self, device_name):
        traceback.print_exc()
        super(DeviceGetInfoFailed, self).__init__(device_name)
