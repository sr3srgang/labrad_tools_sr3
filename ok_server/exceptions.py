import traceback

class BitfileNotFound(Exception):
    def __init__(self, bitfile_name):
        traceback.print_exc()
        message = bitfile_name
        super(BitfileNotFound, self).__init__(message)

