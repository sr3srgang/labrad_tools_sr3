import numpy as np

def seconds_to_ticks(time, clk):
    return  int(round(time * clk))

def volts_to_bits(voltage, voltage_range, dac_bits):
    min_voltage = min(voltage_range)
    max_voltage = max(voltage_range)
    voltage_span = float(max_voltage - min_voltage)
    voltage = sorted([-voltage_span, voltage, voltage_span])[1]
    return int(round(voltage / voltage_span * (2**dac_bits - 1)))

def shift_bits(ticks):
    return int(np.log2(ticks)) + 2

def get_ramp_bytes(bits, ticks):
    shift = shift_bits(ticks)
    signed_ramp_rate = int((bits * 2**shift / ticks)) + 1
    rate_bits = '{:018b}'.format(signed_ramp_rate & 0b111111111111111111)
    tick_bits = '{:030b}'.format(ticks)
    ramp_bits = tick_bits + rate_bits
    return [int(ramp_bits[::-1][i:i+8][::-1], 2) for i in range(0, 48, 8)]
