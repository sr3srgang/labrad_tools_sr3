import traceback

class ChannelNotFound(Exception):
    def __init__(self, channel_id):
        traceback.print_exc()
        message = '{}'.format(channel_id)
        super(ChannelNotFound, self).__init__(message)
