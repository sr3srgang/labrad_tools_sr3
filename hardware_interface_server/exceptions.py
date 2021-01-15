import traceback

class InterfaceAlreadyOpen(Exception):
    def __init__(self, interface_id):
        traceback.print_exc()
        message = interface_id
        super(InterfaceAlreadyOpen, self).__init__(message)

class InterfaceNotAvailable(Exception):
    def __init__(self, interface_id):
        traceback.print_exc()
        message = interface_id
        super(InterfaceNotAvailable, self).__init__(message)
