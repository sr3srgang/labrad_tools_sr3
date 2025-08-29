from transport_xrf.constants import *
import numpy as np
from pathlib import Path  # updated
from typing import Tuple, Callable

class Transport:
    DEBUG_MODE = False
    # DEBUG_MODE = True
    def _print_debug(self, str):
        if self.DEBUG_MODE is not True:
            return
        print("[DEBUG] " + str + "\n\tfrom " + __file__)
    
    SCRIPT_DIR = Path(__file__).parent.parent / "table scripts"
    TEMPLATE_DIR = Path(__file__).parent
    
    # defined functional forms of transport
    # the key refers to the form of transport distance vs time
    # the value is the callable for velocity vs time (i.e., the derivative of the distance function)
    forms = {
        "linear": lambda t: np.ones_like(t),
        "quadratic": lambda t: 2*t,
        "sine": lambda t: 2*np.sin(np.pi*t)**2,
        "minjerk": lambda t: 30*t**2*(1 - t)**2
    }
        
    def __init__(self):
        """load templates for header and foother of table scripts"""

        template_path = self.TEMPLATE_DIR / "TPA_header_template.txt"
        with open(template_path, "r") as file:
            header_template_script = file.read()
        self.header_template_script = header_template_script
   
        template_path = self.TEMPLATE_DIR/ "TPA_footer_template.txt"
        with open(template_path, "r") as file:
            footer_template_script = file.read()
        self.footer_template_script = footer_template_script
        
        self._print_debug("Transport templates loaded.")
        
    
    def _get_ramp_arguments(self, T: float, dfi: float, dff: float, res_df: float) -> Tuple[float, float]:
        """Return the argument values to pass in TABLE,RAMP entry.

        Args:
            T (float): duration of the ramp
            dfi (float): initial frequency deviation
            dff (float): final frequency deviation
            res_df (float): frequency control resolution

        Returns:
            (float, float): update period and number of updates
        """
        # frequency quanta
        qfi = round(dfi/res_df); qff = round(dff/res_df); qf = qff - qfi
        # time quanta
        qt = round(T / XPARAM_MIN_DURATION)
        if qf >= qt:
            # freq change per time resolution is not smaller than the min freq control resolution
            # set update period to be time resolution
            update_period = XPARAM_MIN_DURATION
            num_update = qt
        else:
            # set update period to be a minimal multiple of the time resolution s.t. time quanta are smaller than freq quanta
            multiplier = np.ceil(qt/abs(qf))
            update_period = multiplier*XPARAM_MIN_DURATION
            num_update = round(T/update_period)
            
        # if t_ramp_step < 1e-6:
        #     t_ramp_step = 1e-6
        #     ramp_step_num = round(t_ramp/t_ramp_step)
        
        return update_period, num_update
    

    def _get_table_entry(self, T: float, dfi: float, dff: float, res_df: float) -> Tuple[str, bool]:
        """Return proper table entry for a given arguments

        Args:
            T (float): duration of the entry
            dfi (float): initial frequency deviation
            dff (float): final frequency deviation
            res_df (float): frequency control resolution

        Returns:
            (str, bool): command string and ramp flag
        """
        # frequency quanta
        qfi = round(dfi/res_df); qff = round(dff/res_df); qf = qff - qfi
        if qf == 0:
            # if there is no change in the discretized frequency, return "hold" entry (a command for constant freq)
            f = BASE_FREQUENCY + dfi
            cmd = f"TABLE,APPEND,1,FREQ,{f}Hz,{T*1e6}us"; is_ramp = False
        else:
            # if there is the frequency change, return "ramp" entry  (a command for ramping freq)
            fi = BASE_FREQUENCY + dfi; ff = BASE_FREQUENCY + dff
            update_period, num_update = self._get_ramp_arguments(T, dfi, dff, res_df)
            cmd = f"TABLE,RAMP,1,FREQ,{fi}Hz,{ff}Hz,{update_period*1e6}us,{num_update}"; is_ramp = True
        
        return cmd, is_ramp
    
        
    def _get_transport_entries(self, func_df: Callable, T: float, phin: float, num_piece: int, res_df: float):
        """
        Return transport entries for a given transport function and parameters. The function is approximated to the piecewise linear functions.
        

        Args:
            func_df (callable): function for frequency deviation vs time
            T (float): transport duration
            phin (float): lattice phase to be transported, normalized by 2*pi
            num_piece (int): number of time pieces to divide the function
            res_df (float): frequency control resolution

        Returns:
            (str, np.ndarray, np.ndarray, float): 
                script for the transport, 
                quantized frequency deviations, 
                ramp flag array, and
                the error in transport distance due to the freq resolution & piecewise approximation of the function
        """
        # digitize in time uniformly by num_piece steps (i.e., num_dt+1 points)
        dt = T / num_piece
        ts = np.linspace(0, 1, num_piece + 1)*T
        dfs0 = func_df(ts/T)*phin/T
        qs_df = np.round(dfs0/res_df) # quanta of df (i.e., integer multiples of df_min)
        dfqs = qs_df*res_df # quantized df
        dfs = dfqs # final df to use
        
        # calculate error in transport distance due to the freq resolution & piecewise approximation of function
        phin_qauntized = np.trapz(dfs, ts) # expected actual phase of discretized signal
        transport_error = phin_qauntized/phin - 1

        # >>> get table entries for a transports >>>
        # first entry to wait for trigger
        script = f"TABLE,APPEND,1,FREQ,{BASE_FREQUENCY}Hz,1us,TRIGDR" + "\n"
        # entries for transport
        are_ramps = np.full(num_piece, None)
        for i in range(num_piece):
            # transport entries for each time piece
            cmd, is_ramp = self._get_table_entry(dt, dfi=dfs[i], dff=dfs[i+1], res_df=res_df)
            are_ramps[i] = is_ramp
            script += cmd + "\n"
        # <<< get table entries for a transports <<<
    
        
        return script, dfs, are_ramps, transport_error



        
    def get_transport_script(self, request):
        # >>> parse transport_xrf conductor parameters >>>
        freq_gain = request["freq_gain"]
        # long transport parameters
        form_long = request["form_long"]
        d_long = request["d_long"]
        t_long = request["t_long"]
        num_piece_long = int(request["num_piece_long"])
        # short transport parameters
        up_down_sequence_short = request["up_down_sequence_short"]
        form_short = request["form_short"]
        d_short = request["d_short"]
        d_short_down = request["d_short_down"]
        t_short = request["t_short"]
        num_piece_short = int(request["num_piece_short"])
        
        # set small transport up and down distances the same if d_short_down conductor parameter has None value
        is_there_short_down = bool(d_short_down) and d_short_down is not None
        if is_there_short_down is False:
            d_short_down = d_short 

        msg_debug = ( 
                     "Got transport parameters:\n"
                     f"\n\tlong: form={form_long}, t={t_long}, d={d_long}"
                     f"\n\tshort: form={form_short}, t={t_short}, d={d_short}"
        )
        if is_there_short_down:
            msg_debug += " (up & down)"
        else:
            msg_debug += f" (up) {d_short_down} (down)"
        self._print_debug(msg_debug)
        
        # <<< parse transport_xrf conductor parameters <<<
        
        
        # >>>>> generate table script >>>>>
        res_df = DDS_FREQ_STEP*2**freq_gain # Hz; XPARAM frequency resolution from given frequency gain
        script = ""
        metadata = {}
        
        # header
        script += self.header_template_script.format(base_freq=f"{BASE_FREQUENCY}Hz", 
                                                     amp=f"{AMPLITUDE}dBm",
                                                     freq_gain=freq_gain)

        # >>> long transport up >>>
        script += "; LONG TRASPORT UP\n\n"
        metadata["long_up"] = {}
        phin_long_up  = d_long/LATTICE_CONSTANT
        if form_long == "legacy":
            raise NotImplementedError("form_long = \"legacy\"")
        else:
            func_df_long_up = self.forms[form_long]
            script_transport_long_up, dfs_long_up, are_ramps_long_up, transport_error_long_up = \
                self._get_transport_entries(func_df_long_up, t_long, phin_long_up, num_piece_long, res_df)
            metadata["long_up"] = {"dfs": dfs_long_up, "are_ramps": are_ramps_long_up, "transport_error": transport_error_long_up}
            script += script_transport_long_up + "\n"
            
        script += "\n\n"
        # <<< long transport up <<<
        

        # >>> short transports >>>
        self._print_debug(f"up_down_sequence_short = {up_down_sequence_short}")
        is_there_short = bool(up_down_sequence_short)
        if is_there_short: # of short transport exist
            script += "; SHORT TRASPORTS\n\n"
            phin_short_up  = d_short/LATTICE_CONSTANT
            phin_short_down  = -d_short_down/LATTICE_CONSTANT
            if form_short == "legacy": 
                raise NotImplementedError("form_short = \"legacy\"")
            else:
                func_df_short = self.forms[form_short]
                script_transport_short_up, dfs_short_up, are_ramps_short_up, transport_error_short_up = \
                    self._get_transport_entries(func_df_short, t_short, phin_short_up, num_piece_short, res_df)
                metadata["short_up"] = {"dfs": dfs_short_up, "are_ramps": are_ramps_short_up, "transport_error": transport_error_short_up}
                script_transport_short_down, dfs_short_down, are_ramps_short_down, transport_error_short_down = \
                    self._get_transport_entries(func_df_short, t_short, phin_short_down, num_piece_short, res_df)
                metadata["short_down"] = {"dfs": dfs_short_down, "are_ramps": are_ramps_short_down, "transport_error": transport_error_short_down}
            
            for multiplier in up_down_sequence_short:
                # self._print_debug(f"multiplier={multiplier}")
                if multiplier == +1:
                    script += "; up\n"
                    script += script_transport_short_up
                else:
                    script += "; down\n"
                    script += script_transport_short_down
            script += "\n\n"
        # <<< short transports <<<

        # footer
        script += self.footer_template_script.format(base_freq=f"{BASE_FREQUENCY}Hz")
        
        return script, metadata


# test script
if __name__ == "__main__":
    import textwrap
    import matplotlib.pylab as plt
    
    # >>> conductor parameter values >>>
    request = {
        "freq_gain": 8,
        "form_long": "minjerk",
        "d_long": 4e-2,
        "t_long": 100e-3,
        "num_piece_long": 21,
        "up_down_sequence_short": [+1, -1, +1, -1],
        "form_short": "sine",
        "d_short": 160e-6,
        "d_short_down": None,
        "t_short": 2e-3,
        "num_piece_short": 11,
    }
    # <<< conductor parameter values <<<
    
    if request["d_short_down"] is None:
        request["d_short_down"] = request["d_short"]
    
    transport = Transport()
    # generate script
    script, metadata = transport.get_transport_script(request)
    
    # print result
    print("script:")
    print(textwrap.indent(script, "\t"))
    print()
    print()
    
    print("metadata:")
    print(textwrap.indent(str(metadata), "\t"))
    print()
    print()
    
    print(
        f"distance error={metadata['long_up']['transport_error']*100:.3f}% (long up)"
        f", {metadata['short_up']['transport_error']*100:.3f}% (short up)"
        f", {metadata['short_down']['transport_error']*100:.3f}% (short down)"
    )
    print()
    
    # save script
    save_path = Path(__file__).parent / f"test_table_script.txt"
    with open(save_path, "w") as file:
        file.write(script)

    # plot
    # = {"long": , "short": ,}
    func_df = {"long": transport.forms[request["form_long"]], "short": transport.forms[request["form_short"]]}
    T = {"long": request["t_long"], "short": request["t_short"],}
    phin = {"long_up": request["d_long"]/LATTICE_CONSTANT, "short_up": request["d_short"]/LATTICE_CONSTANT, "short_down": request["d_short_down"]/LATTICE_CONSTANT}
    num_piece = {"long": request["num_piece_long"], "short": request["num_piece_short"]}
    tsp = {"long": np.linspace(0, 1, 1000)*T["long"], "short": np.linspace(0, 1, 1000)*T["short"],}
    dfsp = {"long_up": func_df["long"](tsp["long"]/T["long"])*phin["long_up"]/T["long"], "short_up": func_df["short"](tsp["short"]/T["short"])*phin["short_up"]/T["short"], "short_down": -func_df["short"](tsp["short"]/T["short"])*phin["short_down"]/T["short"]}
    ts = {"long": np.linspace(0, 1, num_piece["long"] + 1)*T["long"], "short": np.linspace(0, 1, num_piece["short"] + 1)*T["short"]}
    dfs = {"long_up": metadata["long_up"]["dfs"], "short_up": metadata["short_up"]["dfs"], "short_down": metadata["short_down"]["dfs"]}
    are_ramps = {"long_up": metadata["long_up"]["are_ramps"], "short_up": metadata["short_up"]["are_ramps"], "short_down": metadata["short_down"]["are_ramps"]}



    fig, axs = plt.subplots(3, 1, figsize=(4, 8))
    # long up
    ax = axs[0]
    ax.plot(tsp["long"]*1e3, dfsp["long_up"]/1e6, 'b-')
    ax.plot(ts["long"]*1e3, dfs["long_up"]/1e6, "r.--", markersize=8)
    ax.set_xlabel("Time [ms]")
    ax.set_ylabel("Frequency [MHz]")
    ax.set_title("long_up")
    
    # short up
    ax = axs[1]
    ax.plot(tsp["short"]*1e3, dfsp["short_up"]/1e6, 'b-')
    ax.plot(ts["short"]*1e3, dfs["short_up"]/1e6, "r.--", markersize=8)
    ax.set_xlabel("Time [ms]")
    ax.set_ylabel("Frequency [MHz]")
    ax.set_title("short_up")
    
    # short down
    ax = axs[2]
    ax.plot(tsp["short"]*1e3, dfsp["short_down"]/1e6, 'b-')
    ax.plot(ts["short"]*1e3, dfs["short_down"]/1e6, "r.--", markersize=8)
    ax.set_xlabel("Time [ms]")
    ax.set_ylabel("Frequency [MHz]")
    ax.set_title("short_down")

    fig.tight_layout()

    fig.savefig(Path(__file__).parent / "transport.png")

    # for i, is_ramp in enumerate(are_ramps):
    #     if is_ramp:
    #         h = ax.axvspan(ts[i], ts[i+1], color="red", alpha=0.1)
    #     else:
    #         h = ax.axvspan(ts[i], ts[i+1], color="blue", alpha=0.1)
    