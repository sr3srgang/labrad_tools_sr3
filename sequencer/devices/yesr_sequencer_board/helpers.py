from sequencer.devices.yesr_sequencer_board.exceptions import TimeOutOfBoundsError

def time_to_ticks(clk, time):
    ticks = int(round(clk * time))
    if (ticks <= 0) or (ticks > 2**32 - 1):
        raise TimeOutOfBoundsError(time, ticks, clk)
    return ticks

def combine_sequences(subsequence_list):
    combined_sequence = subsequence_list.pop(0)
    for subsequence in subsequence_list:
        for k in subsequence.keys():
            combined_sequence[k] += subsequence[k]
    return combined_sequence

