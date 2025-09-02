import tkinter as tk
import RPi.GPIO as GPIO

# GPIO setup
GPIO.setmode(GPIO.BCM)
led_pins = {"LED 1": 17, "LED 2": 27, "LED 3": 22}
for pin in led_pins.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# Functions
def turn_on_led(led_name):
    for name, pin in led_pins.items():
        GPIO.output(pin, GPIO.HIGH if name == led_name else GPIO.LOW)

def exit_program():
    GPIO.cleanup()
    window.destroy()

# GUI
window = tk.Tk()
window.title("LED Controller")

selected_led = tk.StringVar(value="LED 1")

for name in led_pins.keys():
    tk.Radiobutton(
        window, text=name, variable=selected_led,
        value=name, command=lambda n=name: turn_on_led(n)
    ).pack(anchor="w")

tk.Button(window, text="Exit", command=exit_program).pack()

window.mainloop()
