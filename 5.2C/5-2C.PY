import RPi.GPIO as GPIO
import tkinter as tk

GPIO.setmode(GPIO.BCM)
led_pins = {'Green': 17, 'Yellow': 27, 'Red': 22}

pwm_leds = {}
for color, pin in led_pins.items():
    GPIO.setup(pin, GPIO.OUT)
    pwm_leds[color] = GPIO.PWM(pin, 1000)  
    pwm_leds[color].start(0)

window = tk.Tk()
window.title("LED Brightness Control")

tk.Label(window, text="Adjust LED Brightness:", font=('Arial', 14)).pack(pady=10)

def update_led(color, intensity):
    gamma = 2.2  
    corrected = (float(intensity) / 100) ** gamma * 100
    pwm_leds[color].ChangeDutyCycle(corrected)

def exit_app():
    for pwm in pwm_leds.values():
        pwm.stop()
    GPIO.cleanup()
    window.destroy()

for color in led_pins.keys():
    frame = tk.Frame(window)
    frame.pack(pady=5)
    tk.Label(frame, text=f"{color} LED", width=10, anchor='w', font=('Arial', 12)).pack(side='left')
    tk.Scale(frame, from_=0, to=100, orient='horizontal', length=200,
             command=lambda value, c=color: update_led(c, value)).pack(side='left')

tk.Button(window, text="Exit", command=exit_app, bg='red', fg='white', width=10).pack(pady=15)

window.mainloop()
