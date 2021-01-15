import traceback

class TimeOutOfBoundsError(Exception):
    def __init__(self, time, ticks, clk):
        traceback.print_exc()
        message = 'time {} [s] corresponds to {} {} [Hz] clock cycles'.format(time, ticks, clk)
        super(TimeOutOfBoundsError, self).__init__(message)

