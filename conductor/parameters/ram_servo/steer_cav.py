import json
import os
import time
from data_analysis.cavity_clock.read_data import *
from data_analysis.cavity_clock.helpers import *
from twisted.internet import reactor
from conductor.parameter import ConductorParameter
from data_analysis.PID import PID


class RamServoLock(ConductorParameter):
    autostart = False
    priority = 10
    data_directory = os.path.join(os.getenv('PROJECT_DATA_PATH'), 'data')
    # data_filename = '{}.conductor.json'
    call_in_thread = False
    default = 105.550e6

    def initialize(self, config):
        super(RamServoLock, self).initialize(config)
        self.connect_to_labrad()

        print("config:")
        print(config)
        active = config.get('servo_active')
        self.active = active
        if active:
            default_val = self.server.parameters.get(
                'ram_servo.bare_dac_voltage').value
            if default_val is not None:
                self.default = default_val
            # TUNE THESE!!
            self.PID_params = {"k_prop": -0.5, "t_int": 10, "t_diff": 0,
                               "setpoint": .5,  "dt": 1, "output_default": self.default}
            self.PID = PID(self.PID_params)
            print('Turning on cav ram servo')

    # def update(self):
    #     if self.active:
    #         print('ram servo update at {}'.format(time.time()))

    #         err_sig = self.server.parameters.get(
    #             'ram_servo.bare_dac_voltage').value
    #         if err_sig is not None:
    #             out = self.PID.update(err_sig)
    #             print("new cav aom val from ram servo: {}".format(out))
    #             self.server.parameters.get(
    #                 'ram_servo.cav_aom_813_rigol').set_value_lock(out)


def update(self):
    if self.active:
        print('ram servo update at {}'.format(time.time()))

        err_sig = self.server.parameters.get(
            'ram_servo.bare_dac_voltage').value
        if err_sig is not None:
            # Zero err_sig if out of allowed range (-0.1, 0.1), inclusive at endpoints
            try:
                err_sig = float(err_sig)
            except (TypeError, ValueError):
                print(
                    f"ram servo: non-numeric err_sig {err_sig!r}; skipping update")
                return

            LIMIT = 0.1
            if -LIMIT <= err_sig <= LIMIT:
                err_for_pid = err_sig
            else:
                print(
                    f"ram servo: err_sig {err_sig:+.6f} out of range (±{LIMIT}); zeroing")
                err_for_pid = 0.0

            out = self.PID.update(err_for_pid)
            print("new cav aom val from ram servo: {}".format(out))
            self.server.parameters.get(
                'ram_servo.cav_aom_813_rigol').set_value_lock(out)


Parameter = RamServoLock
