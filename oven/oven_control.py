import socket
import time
from threading import Event, Thread
import datetime
from influxdb.influxdb_write import write_influxdb

DEVICE_IP = "192.168.1.30"
DEVICE_PORT = 23
stop_ramping = Event()

low_value = 3.300  # W
high_value = 8.000  # W
power_step = 0.1  # W
time_step = 70  # second


def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def query_ovenout_value(gui_callback, current_value_callback):
    command = 'ovenout.value?\n'
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((DEVICE_IP, DEVICE_PORT))
        sock.sendall(command.encode('ascii'))
        response = sock.recv(1024).decode('ascii')
        gui_callback(f"{timestamp()} Response from device: {response}")
        current_value_callback(response.split('=')[-1].strip())


def query_current_value():
    command = 'ovenout.value?\n'
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((DEVICE_IP, DEVICE_PORT))
        sock.sendall(command.encode('ascii'))
        response = sock.recv(1024).decode('ascii').strip()
        return float(response.split('=')[-1])


def query_temperature_value():
    command = 'oventemp.value?\n'
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((DEVICE_IP, DEVICE_PORT))
        sock.sendall(command.encode('ascii'))
        response = sock.recv(1024).decode('ascii').strip()
        return float(response.split('=')[-1])


def set_ovenout_value(value, gui_callback):
    command = f'ovenout.value={value}\n'
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((DEVICE_IP, DEVICE_PORT))
        sock.sendall(command.encode('ascii'))
        time.sleep(0.1)
        try:
            sock.settimeout(0.2)
            response = sock.recv(1024)
            gui_callback(
                f"{timestamp()} Value set to {float(value):.3f} successfully with no error response." if not response else f"{timestamp()} Error: {response.decode('ascii')}")
        except socket.timeout:
            gui_callback(
                f"{timestamp()} Value set to {float(value):.3f} successfully with no error response.")


# def ramp_up(gui_callback):
#     current_value = query_current_value()
#     stop_ramping.clear()
#     for value in [current_value + i * power_step for i in range(int((high_value - current_value) / power_step) + 1)]:
#         if stop_ramping.is_set():
#             break
#         set_ovenout_value(value, gui_callback)
#         time.sleep(time_step)

def ramp_up(gui_callback):
    current_value = query_current_value()
    stop_ramping.clear()
    # Calculate the number of steps excluding the final step to high_value
    steps = range(int((high_value - current_value) / power_step))
    for i in steps:
        if stop_ramping.is_set():
            break
        next_value = current_value + i * power_step
        set_ovenout_value(next_value, gui_callback)
        time.sleep(time_step)
    if not stop_ramping.is_set():
        # Ensure the final value is set to high_value
        set_ovenout_value(high_value, gui_callback)


def ramp_down(gui_callback):
    current_value = query_current_value()
    stop_ramping.clear()
    for value in [current_value - i * power_step for i in range(int((current_value - low_value) / power_step) + 1)]:
        if stop_ramping.is_set():
            break
        set_ovenout_value(value, gui_callback)
        time.sleep(time_step)


def oven_off(gui_callback):
    set_ovenout_value(low_value, gui_callback)


def write_to_influxdb():
    while True:
        try:
            queried_value = query_current_value()
            write_influxdb('oven_power', queried_value)
            queried_temp = query_temperature_value()
            write_influxdb('oven_temp', queried_temp)
        except Exception as e:
            print('InfluxDB server not happy:', e)
        time.sleep(15)  # Adjust the sleep time as needed


def start_influxdb_writer():
    writer_thread = Thread(target=write_to_influxdb)
    writer_thread.daemon = True
    writer_thread.start()
