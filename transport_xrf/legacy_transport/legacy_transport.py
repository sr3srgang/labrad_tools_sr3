from transport_xrf.constants import *
import math
from pathlib import Path  # updated
import os

class LegacyTransport:
    DEBUG_MODE = False
    # DEBUG_MODE = True
    def _print_debug(self, str):
        if self.DEBUG_MODE is not True:
            return
        print("[DEBUG] " + str + "\n\tfrom " + __file__)
    
    SCRIPT_DIR = Path(__file__).parent.parent / "table scripts"
    TEMPLATE_DIR = Path(__file__).parent
        
    def __init__(self):
        # load template table scripts for legacy transport

        template_path = self.TEMPLATE_DIR / "TPA_header_template.txt"
        with open(template_path, "r") as file:
            header_template_script = file.read()
        self.header_template_script = header_template_script

        template_path = self.TEMPLATE_DIR / "TPA_transport_template.txt"
        with open(template_path, "r") as file:
            transport_template_script = file.read()
        self.transport_template_script = transport_template_script
   
        template_path = self.TEMPLATE_DIR/ "TPA_footer_template.txt"
        with open(template_path, "r") as file:
            footer_template_script = file.read()
        self.footer_template_script = footer_template_script
        print("Legacy tranport templates loaded.")
        
    def _get_freq_sweep_amplitude_gain(self, d, t_ramp, t_hold):
        # get freq sweep amplitude Af
        phin = d/LATTICE_CONSTANT
        Af = phin/(t_ramp + t_hold)
        # get freq gain for XPARAM
        # see Section 9.7 in the manual
        freq_bit = math.ceil(math.log2(Af/DDS_FREQ_STEP)) + 1 # "+ 1" for sign of freq shift
        freq_gain = freq_bit - XPARAM_BIT # see Fig. 9.4
        if freq_gain > XPARAM_MAX_FREQ_GAIN:
            max_Af = DDS_FREQ_STEP*2**(XPARAM_BIT-1 + XPARAM_MAX_FREQ_GAIN) # Hz; -1 for sign
            raise ValueError(
                f"Frequency sweep amplitude `Af` for the given transport distance and duration exceeds the maximum value supported = {max_Af/1e3} kHz"
                f"\n\tAf = {Af/1e3} kHz for distance = {d*1e6} um and durations t_ramp={t_ramp*1e6} us & t_hold = {t_hold*1e6} us."
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
            
        # if t_ramp_step < 1e-6:
        #     t_ramp_step = 1e-6
        #     ramp_step_num = round(t_ramp/t_ramp_step)
        
        return t_ramp_step, ramp_step_num
    
    def _get_transport_entries(self, Af, t_ramp_step, ramp_step_num, t_hold):
        msg = "_get_transport_entries() called."
        msg += f"\n\tAf={Af}, t_ramp_step={t_ramp_step}, ramp_step_num={ramp_step_num}, t_hold={t_hold}"
        self._print_debug(msg)
        freq_to_ramp = BASE_FREQUENCY + Af
        self._print_debug(f"\n\tBASE_FREQUENCY={BASE_FREQUENCY}, Af={Af}, freq_to_ramp={freq_to_ramp}")
        return self.transport_template_script.format(
            base_freq=f"{BASE_FREQUENCY/1e6}MHz",
            freq_to_ramp=f"{freq_to_ramp/1e6}MHz",
            t_ramp_step=f"{t_ramp_step*1e6}us",
            ramp_step_num=f"{ramp_step_num}",
            t_hold=f"{t_hold*1e6}us",
        )
        
        
        
        
        
        
    def get_transport_script(self, request):
        freq_gain = request["freq_gain"]
        d_long = request["d_long"]
        t_long = request["t_long"]
        d_short = request["d_short"]
        t_short = request["t_short"]
        #MM 20250617
        d_short_down = request["d_short_down"]
        up_down_sequence_short = request["up_down_sequence_short"]
        
        msg_debug = ( 
                     "Got transport parameters:\n"
                     f"\n\tlong: x={d_long}, d={t_long}"
                     f"\n\tshort: x={d_short}, d={t_short}"
        )
        self._print_debug(msg_debug)
        
        # ramp and hold times
        # t_ramp_long = t_long/3
        # t_hold_long = t_long/3
        # t_ramp_short = t_short/3
        # t_hold_short = t_short/3
        t_ramp_long = t_long*55/140
        t_hold_long = t_long*30/140
        t_ramp_short = t_short*1/2.5
        t_hold_short = t_short*0.5/2.5
        
        
        # calcualte freq sweep amplitudes and freq gains for long and short transports
        Af_long, _ = self._get_freq_sweep_amplitude_gain(d_long,  t_ramp_long, t_hold_long)
        print(f"d_long={d_long}, t_ramp_long={t_ramp_long}, t_hold_long={t_hold_long}, Af_long={Af_long}")
        Af_short, _ = self._get_freq_sweep_amplitude_gain(d_short, t_ramp_short, t_hold_short)
        # print(f"d_short={d_short}, t_ramp_short={t_ramp_short}, t_hold_short={t_hold_short}, Af_short={Af_short}")
        Af_short_down, _ = self._get_freq_sweep_amplitude_gain(d_short_down, t_ramp_short, t_hold_short)
        # calculate time step duration and numbers in RAMP entry
        # t_ramp_step_long, ramp_step_num_long = self._get_ramp_duration_number(t_ramp_long, Af_long, freq_gain_long)
        t_ramp_step_long, ramp_step_num_long = self._get_ramp_duration_number(t_ramp_long, Af_long, freq_gain)
        # ramp_step_num_long = 200
        # t_ramp_step_long = t_ramp_long/ramp_step_num_long
        
        # t_ramp_step_short, ramp_step_num_short = self._get_ramp_duration_number(t_ramp_short, Af_short, freq_gain_short)
        t_ramp_step_short, ramp_step_num_short = self._get_ramp_duration_number(t_ramp_short, Af_short, freq_gain)
        t_ramp_step_short_down, ramp_step_num_short_down = self._get_ramp_duration_number(t_ramp_short, Af_short_down, freq_gain)

                
        # variable to store the script to send to Moglabs XRF
        script = ""

        # load & format templates
        # # header
        script += self.header_template_script.format(base_freq=f"{BASE_FREQUENCY/1e6}MHz", 
                                                     amp=f"{AMPLITUDE}dBm",
                                                     freq_gain=freq_gain)

        # # transports
            
        # # # long transport up
        script += "; LONG TRASPORT UP\n\n"
        script += self._get_transport_entries(Af_long, t_ramp_step_long, ramp_step_num_long, t_hold_long)
        script += "\n"
        # # short transports
        # print("SEQUENCE:", up_down_sequence_short)
        if up_down_sequence_short:
            self._print_debug(f"up_down_sequence_short={up_down_sequence_short}")
            script += "; SHORT TRASPORTS\n\n"
            # script += f"TABLE,XPARAM,1,FREQ,{freq_gain_short}\n\n" # step resolution = 7.45 Hz
            for multiplier in up_down_sequence_short:
                # self._print_debug(f"multiplier={multiplier}")
                if multiplier == +1:
                    script += "; up\n"
                    Af = multiplier*Af_short
                    script += self._get_transport_entries(Af, t_ramp_step_short, ramp_step_num_short, t_hold_short)
                else:
                    script += "; down\n"
                    Af = multiplier*Af_short_down
                    script += self._get_transport_entries(Af, t_ramp_step_short_down, ramp_step_num_short_down, t_hold_short)


        # # footer
        script += self.footer_template_script.format(base_freq=f"{BASE_FREQUENCY/1e6}MHz")
        
        # if self.DEBUG_MODE:
        #     save_path = self.SCRIPT_DIR / "DEBUG_legacy_table_script.txt"
        #     self._print_debug(f"Saving generated script to {save_path} ...")
        #     with open(save_path, "w") as file:
        #         file.write(script)
        #     self._print_debug("Saved.")
            
        save_path = self.SCRIPT_DIR / "legacy_table_script.txt"
        print(f"Saving generated script to {save_path} ...", end=" ")
        with open(save_path, "w") as file:
            file.write(script)
        print("Done.")
        
        Af = {"long": Af_long, "short": Af_short, "short_down": Af_short_down*-1}
        t_ramp_step = {"long": t_ramp_step_long, "short": t_ramp_step_short, "short_down": t_ramp_step_short_down}
        ramp_step_num = {"long": ramp_step_num_long, "short": ramp_step_num_short, "short_down": ramp_step_num_short_down}
        
        return script, freq_gain, Af, t_ramp_step, ramp_step_num
