import tkinter as tk
import RPi.GPIO as GPIO

# GPIO setup
GPIO.setmode(GPIO.BCM)
led_pins = {"LED 1": 17, "LED 2": 27, "LED 3": 22}

# Setup LEDs with PWM
pwm_objects = {}
for name, pin in led_pins.items():
    GPIO.setup(pin, GPIO.OUT)
    pwm = GPIO.PWM(pin, 100)  # 100 Hz frequency
    pwm.start(0)  # Start with 0% duty cycle (off)
    pwm_objects[name] = pwm

# Functions
def set_brightness(led_name, value):
    duty_cycle = int(value)  # slider gives string, convert to int
    pwm_objects[led_name].ChangeDutyCycle(duty_cycle)

def exit_program():
    for pwm in pwm_objects.values():
        pwm.stop()
    GPIO.cleanup()
    window.destroy()

# GUI setup
window = tk.Tk()
window.title("LED Brightness Controller")

# Create sliders for each LED
for name in led_pins.keys():
    tk.Label(window, text=name).pack()
    slider = tk.Scale(
        window, from_=0, to=100, orient="horizontal",
        command=lambda val, n=name: set_brightness(n, val)
    )
    slider.pack()

tk.Button(window, text="Exit", command=exit_program).pack()

window.mainloop()
