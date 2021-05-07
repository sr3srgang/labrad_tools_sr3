import numpy as np
import os
from conductor.parameter import ConductorParameter

class Picoscope(ConductorParameter):
    autostart = True
    priority = -1

    record_keyword = 'save'
    keyword = 'pico'

