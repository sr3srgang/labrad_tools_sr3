import os

# parameters for trasport
base_freq = 110e6  # Hz
amp = 30 # dBm
# # long transport up
x_long = 40e-3 # m
d_long = 30e-3 # s
# # short transports
x_short = 110e-6 # m
d_short = 3e-3 # s


LATTICE_WAVELENGTH = 813.428e-9 # m
LATTICE_CONSTANT = LATTICE_WAVELENGTH/2 # m

# variable to store the script to send to Moglabs XRF
script = ""

# Ensure the working directory is set to the script's directory
script_dir = os.path.dirname(__file__)


# load & format templates
# # header
template_file = os.path.join(script_dir, "TPA_header_template.txt")
with open(template_file, "r") as file:
    template_script = file.read()
script += template_script.format(base_freq=f"{base_freq/1e6}MHz", amp=f"{amp}dBm")

# # transports
template_file = os.path.join(script_dir, "TPA_transport_template.txt")
with open(template_file, "r") as file:
    template_script = file.read()

def generate_transport_entries(x, d):
    phin = x/LATTICE_CONSTANT
    df = 3*phin/2/d
    t_ramp = t_hold = d / 3
    ramp_step_num = 1000 # TBD
    t_ramp_step = t_ramp / ramp_step_num
    freq_to_ramp = base_freq + df
    
    return template_script.format(
    base_freq=f"{base_freq/1e6}MHz",
    freq_to_ramp=f"{freq_to_ramp/1e6}MHz",
    t_ramp_step=f"{t_ramp_step*1e6}us",
    ramp_step_num=f"{ramp_step_num}",
    t_hold=f"{t_hold*1e6}us",
)
    
# # # long transport up
script += "# LONG TRASPORT UP\n\n"
script += generate_transport_entries(x_long, d_long)

# # short transports
# # # up
script += generate_transport_entries(x_short, d_short)
# # # up
script += generate_transport_entries(-x_short, d_short)

# # footer
template_file = os.path.join(script_dir, "TPA_footer_template.txt")
with open(template_file, "r") as file:
    template_script = file.read()
script += template_script.format(base_freq=f"{base_freq/1e6}MHz")


print("script:")
print()
print(script)
print()
print()

