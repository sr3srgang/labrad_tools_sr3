from picoscope import ps3000a
from time import sleep
import matplotlib.pyplot as plt
import numpy as np
import time
import labrad
import json

cxn = labrad.connect()

SERIAL_NUMBER = "DU009/008"
N_TRIG = 3
DATA_FILENAME = './data.json'

ps = ps3000a.PS3000a(SERIAL_NUMBER)

ps.setChannel("A", coupling="DC", VRange=5.0, probeAttenuation=10)
ps.setChannel("B", enabled=False)
ps.setChannel("C", enabled=False)
ps.setChannel("D", enabled=False)
res = ps.setSamplingFrequency(1e9, int(1e6))
print("Sampling @ %f MHz, %d samples"%(res[0]/1e6, res[1]))
#Use external trigger to mark when we sample
ps.setSimpleTrigger(trigSrc="External", threshold_V=2, timeout_ms=-1)
samples_per_segment = ps.memorySegments(N_TRIG)
ps.setNoOfCaptures(N_TRIG)
#data = np.zeros((N_TRIG, samples_per_segment), dtype=np.int16)

def go():
    ps.runBlock()
    
    print("Waiting for trigger")
    while(ps.isReady() == False): 
        time.sleep(0.01)
    ti = time.time()
    print("Sampling Done")
    sums = {}
    data = {}
    for i in range(N_TRIG):
        response = ps.getDataV("A", 50000, segmentIndex=i)
        data[i] = response
        sums[i] = sum(response)

    tot = (sums[0] + sums[1] - 2 * sums[2])
    frac = (sums[0] - sums[2]) / tot
    data = {
        'gnd': data[0].tolist(),
        'exc': data[1].tolist(),
        'bac': data[2].tolist(),
        'frac': frac,
        'tot': tot,
    }
    cxn.conductor.set_parameter_values(
        json.dumps({
            'pico': {
                'frac': frac,
                'tot': tot,
            }
        }),
        True,
        'data',
    )
    with open(DATA_FILENAME, 'w') as outfile:
        json.dump(data, outfile)

    print "excitation frac", frac
    print "total", tot
    tf = time.time()
    print "readout time: ", tf-ti

#    for i in range(N_TRIG):
#        plt.plot(data[i])
#    plt.savefig('test.pdf')
#
while 1:
    go()
