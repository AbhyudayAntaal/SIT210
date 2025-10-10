import RPi.GPIO as GPIO
import tkinter as tk

GPIO.setmode(GPIO.BCM)
led_pins = {'Green': 17, 'Yellow': 27, 'Red': 22}
for pin in led_pins.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

def turn_on_led(color):
    for name, pin in led_pins.items():
        GPIO.output(pin, GPIO.HIGH if name == color else GPIO.LOW)

def exit_app():
    GPIO.cleanup()
    window.destroy()

window = tk.Tk()
window.title("LED Controller")

tk.Label(window, text="Select LED to Turn On:", font=('Arial', 14)).pack(pady=10)

selected_led = tk.StringVar(value="None")
for color in led_pins.keys():
    tk.Radiobutton(window, text=color, variable=selected_led,
                   value=color, command=lambda: turn_on_led(selected_led.get()),
                   font=('Arial', 12)).pack(anchor='w')

tk.Button(window, text="Exit", command=exit_app, bg='red', fg='white', width=10).pack(pady=15)

window.mainloop()
