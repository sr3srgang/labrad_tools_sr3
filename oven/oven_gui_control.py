import tkinter as tk
from tkinter import scrolledtext, messagebox, Toplevel
import datetime
import threading

# Import the device control functions from the other script
from oven_control import query_ovenout_value, set_ovenout_value, ramp_up, ramp_down, stop_ramping, oven_off, start_influxdb_writer


def update_output(message):
    text_area.configure(state='normal')
    text_area.insert(tk.INSERT, message + "\n")
    text_area.see(tk.INSERT)
    text_area.configure(state='disabled')


def update_current_value(value):
    current_value_display.configure(state='normal')
    current_value_display.delete(0, tk.END)
    current_value_display.insert(0, value)
    current_value_display.configure(state='readonly')


def gui_query_value():
    threading.Thread(target=query_ovenout_value, args=(
        update_output, update_current_value)).start()


def gui_set_value():
    value = value_entry.get()
    if value:
        threading.Thread(target=set_ovenout_value,
                         args=(value, update_output)).start()


def gui_ramp_up():
    threading.Thread(target=ramp_up, args=(update_output,)).start()


def gui_ramp_down():
    threading.Thread(target=ramp_down, args=(update_output,)).start()


def gui_stop_ramp():
    stop_ramping.set()
    update_output("Ramp process stopped.")


def gui_oven_off():
    threading.Thread(target=oven_off, args=(update_output,)).start()


def schedule_ramp_up():
    def on_yes():
        # Schedule the ramp_up function to run tomorrow at 7 AM
        now = datetime.datetime.now()
        target_time = datetime.datetime.combine(
            now.date() + datetime.timedelta(days=1), datetime.time(7, 0))
        delay = (target_time - now).total_seconds()
        threading.Timer(delay, lambda: ramp_up(update_output)).start()
        update_output(
            f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Scheduled ramp up for tomorrow at 7 AM")
        schedule_window.destroy()

    def on_no():
        update_output(
            f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Ramp up scheduling cancelled")
        schedule_window.destroy()

    schedule_window = Toplevel(root)
    schedule_window.title("Schedule Ramp Up")
    message = tk.Label(
        schedule_window, text="Schedule a ramp up for tomorrow at 7 AM?")
    message.pack()
    yes_button = tk.Button(schedule_window, text="Yes", command=on_yes)
    yes_button.pack(side=tk.LEFT)
    no_button = tk.Button(schedule_window, text="No", command=on_no)
    no_button.pack(side=tk.RIGHT)


def schedule_ramp_up_at():
    def on_schedule():
        date_str = date_entry.get()
        time_str = time_entry.get()
        try:
            target_datetime = datetime.datetime.strptime(
                f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            now = datetime.datetime.now()
            if target_datetime > now:
                delay = (target_datetime - now).total_seconds()
                threading.Timer(delay, lambda: ramp_up(update_output)).start()
                update_output(
                    f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Scheduled ramp up for {target_datetime.strftime('%Y-%m-%d %H:%M')}")
                schedule_window.destroy()
            else:
                messagebox.showerror(
                    "Invalid Time", "Scheduled time must be in the future.")
        except ValueError:
            messagebox.showerror(
                "Invalid Format", "Please enter date and time in the correct format.")

    schedule_window = Toplevel(root)
    schedule_window.title("Schedule Ramp Up at Specific Time")

    tk.Label(schedule_window, text="Enter date (YYYY-MM-DD):").pack()
    date_entry = tk.Entry(schedule_window)
    date_entry.pack()

    tk.Label(schedule_window, text="Enter time (HH:MM):").pack()
    time_entry = tk.Entry(schedule_window)
    time_entry.pack()

    schedule_button = tk.Button(
        schedule_window, text="Schedule", command=on_schedule)
    schedule_button.pack()


def modified_gui_oven_off():
    threading.Thread(target=oven_off, args=(update_output,)).start()
    schedule_ramp_up()


root = tk.Tk()
root.title("Oven Control")

current_value_label = tk.Label(root, text="Current value")
current_value_label.grid(column=0, row=0, sticky="w")
current_value_display = tk.Entry(root, state='readonly')
current_value_display.grid(column=1, row=0, sticky="ew")

set_value_label = tk.Label(root, text="Set Value")
set_value_label.grid(column=0, row=1, sticky="w")
value_entry = tk.Entry(root)
value_entry.grid(column=1, row=1, sticky="ew")

button_frame = tk.Frame(root)
button_frame.grid(column=2, row=0, rowspan=5, sticky="ns")

query_button = tk.Button(
    button_frame, text="Query Value", command=gui_query_value)
set_button = tk.Button(button_frame, text="Set Value", command=gui_set_value)
ramp_up_button = tk.Button(button_frame, text="Ramp Up", command=gui_ramp_up)
ramp_down_button = tk.Button(
    button_frame, text="Ramp Down", command=gui_ramp_down)
stop_ramp_button = tk.Button(
    button_frame, text="Stop Ramp", command=gui_stop_ramp)
oven_off_button = tk.Button(
    button_frame, text="Oven Off", command=modified_gui_oven_off)
schedule_ramp_up_button = tk.Button(
    button_frame, text="Schedule Ramp Up", command=schedule_ramp_up)
schedule_ramp_up_at_button = tk.Button(
    button_frame, text="Schedule Ramp Up at Specific Time", command=schedule_ramp_up_at)

query_button.pack(fill=tk.X)
set_button.pack(fill=tk.X)
ramp_up_button.pack(fill=tk.X)
ramp_down_button.pack(fill=tk.X)
stop_ramp_button.pack(fill=tk.X)
oven_off_button.pack(fill=tk.X)
schedule_ramp_up_button.pack(fill=tk.X)
schedule_ramp_up_at_button.pack(fill=tk.X)

text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD)
text_area.grid(column=0, row=2, columnspan=2, sticky="ew")

# Start InfluxDB writer thread
start_influxdb_writer()

root.mainloop()
