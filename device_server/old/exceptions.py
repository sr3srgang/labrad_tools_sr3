import traceback

class DeviceAlreadyInitializedError(Exception):
    def __init__(self, device_name):
        traceback.print_exc()
        message = device_name
        super(DeviceAlreadyInitializedError, self).__init__(message)

class DeviceInitializationError(Exception):
    def __init__(self, device_name):
        traceback.print_exc()
        message = device_name
        super(DeviceInitializationFailed, self).__init__(message)

class DeviceTerminationError(Exception):
    def __init__(self, device_name):
        traceback.print_exc()
        message = device_name
        super(DeviceTerminationFailed, self).__init__(message)

class DeviceImportError(Exception):
    def __init__(self, device_name):
        traceback.print_exc()
        message = device_name
        super(DeviceImportFailed, self).__init__(message)
