import socket
import tkinter as tk
from tkinter import ttk
import threading
import datetime
from influxdb.influxdb_write import write_influxdb
import time

# Power supply IP address and port
POWER_SUPPLY_IP = '192.168.1.31'  # Your specific power supply IP address
POWER_SUPPLY_PORT = 8462          # Default port number for PSC-ETH-2
TIMEOUT_DURATION = 0.2  # Timeout for socket communication in seconds

# Default values for ramping
Low_V_Out = 7
High_V_Out = 16
RAMP_DURATION_MINUTES = 60  # Total ramping time in minutes

# Function to send a command to the power supply and read the response


def send_command(command):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT_DURATION)
        sock.connect((POWER_SUPPLY_IP, POWER_SUPPLY_PORT))
        sock.sendall((command + '\n').encode('ascii'))
        response = sock.recv(1024)
        return response.decode('ascii').strip()
    except socket.timeout:
        return "Error: Connection timed out."
    except socket.error as e:
        return f"Error: {str(e)}"
    finally:
        sock.close()

# Function to ramp up the voltage


def ramp_up_voltage():
    try:
        low_v = float(low_v_entry.get())
        high_v = float(high_v_entry.get())
        voltage_increment = (high_v - low_v) / RAMP_DURATION_MINUTES
        for minute in range(RAMP_DURATION_MINUTES + 1):
            current_voltage = low_v + minute * voltage_increment
            send_command(f'SOURce:VOLTage {current_voltage}')
            # Run the measure_all function after setting each new voltage value
            measure_all()
            progress_var.set((minute / RAMP_DURATION_MINUTES) * 100)
            remaining_time_var.set(
                f"{RAMP_DURATION_MINUTES - minute} minutes")
            root.update_idletasks()
            time.sleep(60)
    except Exception as e:
        print(f"Error during ramping up: {e}")

# Function to measure voltage, current, and power


def measure_all():
    voltage_result.set(f"{send_command('MEASure:VOLTage?')} V")
    current_result.set(f"{send_command('MEASure:CURRent?')} A")
    power_result.set(f"{send_command('MEASure:POWer?')} W")

# Function to set output voltage


def set_voltage():
    voltage = voltage_entry.get()
    send_command(f'SOURce:VOLTage {voltage}')
    time.sleep(0.3)
    measure_all()

# Function to set output current


def set_current():
    current = current_entry.get()
    send_command(f'SOURce:CURRent {current}')
    time.sleep(0.3)
    measure_all()

# Function to set voltage to Low_V_Out


def low_voltage_mode():
    low_v = low_v_entry.get()
    send_command(f'SOURce:VOLTage {low_v}')
    voltage_result.set(f"Set to Low Voltage: {low_v} V")


def schedule_ramp_up():
    # Get the current time
    now = datetime.datetime.now()

    # Determine the target time for ramp up (7am)
    target_time = now.replace(hour=7, minute=0, second=0, microsecond=0)

    # If current time is between 7am and 12am, schedule for tomorrow at 7am
    if now.hour >= 7 and now.hour < 24:
        target_time += datetime.timedelta(days=1)
    # If current time is between 12am and 7am, schedule for today at 7am

    # Calculate the delay time in seconds
    delay_seconds = (target_time - now).total_seconds()

    # Display scheduling information
    print(f"Scheduled ramp-up at {target_time}")

    # Start a thread that waits and then runs the ramp_up_voltage
    threading.Timer(delay_seconds, ramp_up_voltage).start()

# Wrapper to run a function in a separate thread


def run_in_thread(target_function):
    threading.Thread(target=target_function, daemon=True).start()

# Function to write voltage, current, and power data to InfluxDB


def write_to_influxdb():
    while True:
        try:
            # Query the current measurements from the power supply
            queried_voltage = send_command('MEASure:VOLTage?')
            write_influxdb('power_supply_voltage', queried_voltage)

            queried_current = send_command('MEASure:CURRent?')
            write_influxdb('power_supply_current', queried_current)

            queried_power = send_command('MEASure:POWer?')
            write_influxdb('power_supply_power', queried_power)

        except Exception as e:
            print('InfluxDB server not happy:', e)
        time.sleep(15)  # Adjust the sleep time as needed

# Function to start the InfluxDB writer thread


def start_influxdb_writer():
    writer_thread = threading.Thread(target=write_to_influxdb)
    writer_thread.daemon = True  # Ensure thread exits when the main program does
    writer_thread.start()

# Call the start_influxdb_writer() function to begin writing data to InfluxDB


# Create the main application window
root = tk.Tk()
root.title("Power Supply Control Interface")

# Create StringVars for holding measurement results
voltage_result = tk.StringVar()
current_result = tk.StringVar()
power_result = tk.StringVar()
remaining_time_var = tk.StringVar()

# Layout according to the image
# Measurements section
measurement_label = tk.Label(root, text="Measurements", font=("Arial", 14))
measurement_label.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

measure_button = tk.Button(
    root, text="Measure", width=15, command=lambda: run_in_thread(measure_all))
measure_button.grid(row=1, column=0, columnspan=2, padx=10, pady=0)

voltage_label = tk.Label(root, text="Voltage")
voltage_label.grid(row=2, column=0, padx=0, pady=5)
voltage_display = tk.Entry(
    root, textvariable=voltage_result, state='readonly', width=10)
voltage_display.grid(row=2, column=1, padx=5, pady=5)

current_label = tk.Label(root, text="Current")
current_label.grid(row=3, column=0, padx=0, pady=5)
current_display = tk.Entry(
    root, textvariable=current_result, state='readonly', width=10)
current_display.grid(row=3, column=1, padx=5, pady=5)

power_label = tk.Label(root, text="Power")
power_label.grid(row=4, column=0, padx=10, pady=5)
power_display = tk.Entry(root, textvariable=power_result,
                         state='readonly', width=10)
power_display.grid(row=4, column=1, padx=5, pady=5)

# Ramp section
ramp_label = tk.Label(root, text="Ramp Voltage", font=("Arial", 14))
ramp_label.grid(row=5, column=0, columnspan=2, padx=10, pady=5)

low_v_label = tk.Label(root, text="Low voltage")
low_v_label.grid(row=6, column=0, padx=10, pady=5)
low_v_entry = tk.Entry(root, width=10)
low_v_entry.insert(0, f"{Low_V_Out} V")
low_v_entry.grid(row=6, column=1, padx=5, pady=5)

high_v_label = tk.Label(root, text="High voltage")
high_v_label.grid(row=7, column=0, padx=10, pady=5)
high_v_entry = tk.Entry(root, width=10)
high_v_entry.insert(0, f"{High_V_Out} V")
high_v_entry.grid(row=7, column=1, padx=5, pady=5)

low_voltage_button = tk.Button(
    root, text="Set Low", width=10, command=lambda: run_in_thread(low_voltage_mode))
low_voltage_button.grid(row=5, column=3, columnspan=1, padx=10, pady=5)

# Output section
output_label = tk.Label(root, text="Output", font=("Arial", 14))
output_label.grid(row=0, column=2, columnspan=2, padx=10, pady=10)

set_voltage_label = tk.Label(root, text="Set voltage (V)")
set_voltage_label.grid(row=1, column=2, padx=10, pady=5)
voltage_entry = tk.Entry(root, width=10)
voltage_entry.grid(row=1, column=3, padx=5, pady=5)
set_voltage_button = tk.Button(
    root, text="Set", command=lambda: run_in_thread(set_voltage))
set_voltage_button.grid(row=1, column=4, padx=5, pady=5)

set_current_label = tk.Label(root, text="Set current (A)")
set_current_label.grid(row=2, column=2, padx=10, pady=5)
current_entry = tk.Entry(root, width=10)
current_entry.grid(row=2, column=3, padx=5, pady=5)
set_current_button = tk.Button(
    root, text="Set", command=lambda: run_in_thread(set_current))
set_current_button.grid(row=2, column=4, padx=5, pady=5)

# Ramp up button
ramp_up_button = tk.Button(
    root, text="Ramp Up", width=10, command=lambda: run_in_thread(ramp_up_voltage))
ramp_up_button.grid(row=5, column=2, columnspan=1, padx=10, pady=5)

# Progress bar and remaining time
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
progress_bar.grid(row=6, column=2, columnspan=2, padx=1, pady=1)

remaining_time_label = tk.Label(root, text="Remaining time:")
remaining_time_label.grid(row=7, column=2, padx=10, pady=5)
remaining_time_display = tk.Entry(
    root, textvariable=remaining_time_var, state='readonly', width=10)
remaining_time_display.grid(row=7, column=3, padx=5, pady=5)

# Button for scheduling the ramp up
schedule_ramp_up_button = tk.Button(
    root, text="Schedule Ramp Up", width=15, command=schedule_ramp_up)
schedule_ramp_up_button.grid(row=8, column=0, columnspan=2, padx=10, pady=5)

# Start InfluxDB writer thread
start_influxdb_writer()

# Start the GUI loop
root.mainloop()
