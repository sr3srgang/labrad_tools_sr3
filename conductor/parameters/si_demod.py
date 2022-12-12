#MM 12122022 copied from sr1

import json
import time
import os
import traceback

from conductor.parameter import ConductorParameter
import vxi11

class SiDemod(ConductorParameter):
    priority = 6
    autostart = False
    def initialize(self, config):
        self.inst = vxi11.Instrument('128.138.107.33')

    def update(self):
    	response = self.inst.ask('SOUR1:FREQ?')
        self.inst.local()
        self.value = 8 * float(response)

        print('Demod freq: ' + str(self.value))




Parameter = SiDemod
