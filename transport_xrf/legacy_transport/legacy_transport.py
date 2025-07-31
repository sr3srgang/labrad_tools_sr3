from transport_xrf.constants import *
import math
import os

class LegacyTransport:
    DEBUG_MODE = False
    def _print_debug(self, str):
        if self.DEBUG_MODE is not True:
            return
        print("[DEBUG] " + str + "\n\tfrom " + __file__)
    
    def __init__(self):
        # load template table scripts for legacy transport
        script_dir = os.path.dirname(__file__)
        self.script_dir = script_dir
        template_path = os.path.join(script_dir, "TPA_header_template.txt")
        with open(template_path, "r") as file:
            header_template_script = file.read()
        self.header_template_script = header_template_script

        template_path = os.path.join(script_dir, "TPA_transport_template.txt")
        with open(template_path, "r") as file:
            transport_template_script = file.read()
        self.transport_template_script = transport_template_script
   
        template_path = os.path.join(script_dir, "TPA_footer_template.txt")
        with open(template_path, "r") as file:
            footer_template_script = file.read()
        self.footer_template_script = footer_template_script
        print("Legacy tranport templates loaded.")
        
    def _get_freq_sweep_amplitude_gain(self, x, d):
        # get freq sweep amplitude Af
        phin = x/LATTICE_CONSTANT
        Af = 3*phin/2/d
        # get freq gain for XPARAM
        # see Section 9.7 in the manual
        freq_bit = math.ceil(math.log2(Af/DDS_FREQ_STEP)) + 1 # "+ 1" for sign of freq shift
        freq_gain = freq_bit - XPARAM_BIT # see Fig. 9.4
        if freq_gain > XPARAM_MAX_FREQ_GAIN:
            max_Af = DDS_FREQ_STEP*2**(XPARAM_BIT-1 + XPARAM_MAX_FREQ_GAIN) # Hz; -1 for sign
            raise ValueError(
                f"Frequency sweep amplitude `Af` for the given transport distance and duration exceeds the maximum value supported = {max_Af/1e3} kHz"
                f"\n\tAf = {Af/1e3} kHz for distance = {x*1e6} um and duration = {d*1e6} us."
            )
        return Af, freq_gain
    
    def _get_ramp_duration_number(self, t_ramp, Af, freq_gain):
        df = DDS_FREQ_STEP*2**freq_gain # Hz; min freq step size given by the frequency gain in XPARAM
        max_step_num_freq = int(math.floor(Af/df)) # max # of allowed steps from the freq_gain
        max_step_num_duration = int(round(t_ramp / XPARAM_MIN_DURATION)) # max # of allowed steps from the 16 ns time resolution of FPGA--DDS parallet communication
        if max_step_num_freq >= max_step_num_duration:
            # required freq step size per XPARAM_MIN_DURATION is not smaller than the min step size
            # set step duration to be minimum
            t_ramp_step = XPARAM_MIN_DURATION
            ramp_step_num = int(round(t_ramp/t_ramp_step))
        else:
            # set step duration to be a minimul multiple s.t. step numbers are smaller than the maximum for the freq amplitude & gain
            multiplier = math.ceil(max_step_num_duration/max_step_num_freq)
            t_ramp_step = multiplier*XPARAM_MIN_DURATION
            ramp_step_num = round(t_ramp/t_ramp_step)
        
        return t_ramp_step, ramp_step_num
    
    def _get_transport_entries(self, Af, t_ramp_step, ramp_step_num, t_hold):
        freq_to_ramp = BASE_FREQUENCY + Af
        return self.transport_template_script.format(
            base_freq=f"{BASE_FREQUENCY/1e6}MHz",
            freq_to_ramp=f"{freq_to_ramp/1e6}MHz",
            t_ramp_step=f"{t_ramp_step*1e6}us",
            ramp_step_num=f"{ramp_step_num}",
            t_hold=f"{t_hold*1e6}us",
        )
        
    def _get_transport_script(self, request):
        x_long = request["x_long"]
        d_long = request["d_long"]
        x_short = request["x_short"]
        d_short = request["d_short"]
        up_down_sequence_short = request["up_down_sequence_short"]
        
        msg_debug = ( 
                     "Got transport parameters:\n"
                     f"\n\tlong: x={x_long}, d={d_long}"
                     f"\n\tshort: x={x_short }, d={d_short}"
        )
        self._print_debug(msg_debug)
        
        # calcualte freq sweep amplitudes and freq gains for long and short transports
        Af_long, freq_gain_long = self._get_freq_sweep_amplitude_gain(x_long, d_long)
        Af_short, freq_gain_short = self._get_freq_sweep_amplitude_gain(x_short, d_short)
        
        # calculate time step duration and numbers in RAMP entry
        t_ramp_long = d_long/3
        t_ramp_step_long, ramp_step_num_long = self._get_ramp_duration_number(t_ramp_long, Af_long, freq_gain_long)
        t_ramp_short = d_short/3
        t_ramp_step_short, ramp_step_num_short = self._get_ramp_duration_number(t_ramp_short, Af_short, freq_gain_short)
                
        # variable to store the script to send to Moglabs XRF
        script = ""

        # load & format templates
        # # header
        script += self.header_template_script.format(base_freq=f"{BASE_FREQUENCY/1e6}MHz", amp=f"{AMPLITUDE}dBm")

        # # transports
            
        # # # long transport up
        script += "; LONG TRASPORT UP\n\n"
        script += f"TABLE,XPARAM,1,FREQ,{freq_gain_long}\n" # step resolution = 59.6 Hz
        t_hold_long = d_long/3
        script += self._get_transport_entries(Af_long, t_ramp_step_long, ramp_step_num_long, t_hold_long)

        # # short transports
        t_hold_short = d_short/3
        if up_down_sequence_short:
            script += "; SHORT TRASPORTS\n\n"
            script += f"TABLE,XPARAM,1,FREQ,{freq_gain_short}\n" # step resolution = 7.45 Hz
            for multiplier in up_down_sequence_short:
                script += "; up\n" if multiplier == +1 else "; down\n"
                Af = multiplier*Af_short
                script += self._get_transport_entries(Af, t_ramp_step_short, ramp_step_num_short, t_hold_short)

        # # footer
        script += self.footer_template_script.format(base_freq=f"{BASE_FREQUENCY/1e6}MHz")
        
        if self.DEBUG_MODE:
            save_path = os.path.join(self.script_dir, "DEBUG_legacy_table_script.txt")
            self._print_debug(f"Saving generated script to {save_path} ...")
            with open(save_path, "w") as file:
                file.write(script)
            self._print_debug("Saved.")
        
        Af = {"long": Af_long, "short": Af_short}
        freq_gain = {"long": freq_gain_long, "short": freq_gain_short}
        t_ramp_step = {"long": t_ramp_step_long, "short": t_ramp_step_short}
        ramp_step_num = {"long": ramp_step_num_long, "short": ramp_step_num_short}
        
        return script, Af, freq_gain, t_ramp_step, ramp_step_num
    