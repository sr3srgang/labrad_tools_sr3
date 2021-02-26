import json

class UpdateProxy(object):
    def __init__(self, name):
        import labrad
        cxn = labrad.connect()
        self._server = cxn.update
        self.name = name
        self._server.register(name)

    def emit(self, message_json):
        self._server.emit(self.name, json.dumps(message_json))
