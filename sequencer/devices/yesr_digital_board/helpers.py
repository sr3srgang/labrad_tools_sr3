from sequencer.devices.yesr_digital_board.exceptions import TimeOutOfBoundsError

def time_to_ticks(clk, time):
    ticks = int(round(clk * time))
    if (ticks <= 0) or (ticks > 2**32 - 1):
        raise TimeOutOfBoundsError(time, ticks, clk)
    return ticks

def get_output(channel_sequence, t):
    for s in channel_sequence[::-1]:
        if s['t'] <= t:
            return s['out']
