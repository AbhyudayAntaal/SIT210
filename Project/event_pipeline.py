#!/usr/bin/env python3
"""
Hybrid Pothole Detection System
Raspberry Pi 4 + GPS + Camera + Serial link to Arduino Nano 33 IoT
-------------------------------------------------------------------
Function:
- Listens for vibration EVENT messages from Arduino
- Reads GPS coordinates via NEO-6M (UART)
- Captures image using Pi Camera
- Applies OpenCV-based edge + color difference detection
- Saves annotated image + JSON event log
-------------------------------------------------------------------
"""

import serial
import pynmea2
import cv2
import numpy as np
import json
import os
import time
from datetime import datetime

# ---------- CONFIG ----------
ARDUINO_PORT = "/dev/ttyACM0"     # Check via 'ls /dev/ttyACM*'
ARDUINO_BAUD = 115200
GPS_PORT = "/dev/ttyUSB0"         # or /dev/serial0 if connected via GPIO
GPS_BAUD = 9600
SAVE_DIR = "/home/pi/pothole_events"
os.makedirs(SAVE_DIR, exist_ok=True)

# Camera settings
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# Vision thresholds
EDGE_LOW = 50
EDGE_HIGH = 150
COLOR_DIFF_THRESH = 15
AREA_MIN = 300
AREA_MAX = 5000

# ---------- Helper Functions ----------

def get_gps_data():
    try:
        gps = serial.Serial(GPS_PORT, GPS_BAUD, timeout=1)
        for _ in range(20):
            line = gps.readline().decode('ascii', errors='ignore').strip()
            if line.startswith('$GPGGA'):
                msg = pynmea2.parse(line)
                if msg.gps_qual > 0:
                    return {
                        "lat": msg.latitude,
                        "lon": msg.longitude,
                        "alt": msg.altitude,
                        "fix_quality": msg.gps_qual
                    }
        gps.close()
    except Exception:
        pass
    return {"lat": None, "lon": None, "alt": None, "fix_quality": 0}


def capture_image():
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    time.sleep(0.5)
    ret, frame = cam.read()
    cam.release()
    if not ret:
        print("[!] Camera capture failed.")
        return None
    return frame


def detect_pothole(frame):
    # Edge Detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, EDGE_LOW, EDGE_HIGH)

    # Color Difference (light or dark)
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    L, A, B = cv2.split(lab)
    L_blur = cv2.GaussianBlur(L, (21, 21), 0)
    diff = cv2.absdiff(L, L_blur)
    _, mask = cv2.threshold(diff, COLOR_DIFF_THRESH, 255, cv2.THRESH_BINARY)

    # Combine edge + color difference
    combined = cv2.bitwise_and(edges, mask)

    # Find contours
    contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    detected = []
    for c in contours:
        area = cv2.contourArea(c)
        if AREA_MIN < area < AREA_MAX:
            x, y, w, h = cv2.boundingRect(c)
            detected.append((x, y, w, h))

    if detected:
        annotated = frame.copy()
        for (x, y, w, h) in detected:
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 0, 255), 2)
        return True, annotated
    return False, frame


# ---------- Main Loop ----------

def main():
    print("[INFO] Starting event listener...")
    arduino = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=1)

    while True:
        try:
            line = arduino.readline().decode('ascii', errors='ignore').strip()
            if not line:
                continue

            if line.startswith("EVENT"):
                parts = line.split(",")
                if len(parts) < 3:
                    continue

                delta = float(parts[1])
                timestamp = parts[2]
                print(f"[EVENT] Δ={delta:.2f} at {timestamp}")

                gps_data = get_gps_data()
                frame = capture_image()
                if frame is None:
                    continue

                detected, annotated = detect_pothole(frame)

                now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                img_path = os.path.join(SAVE_DIR, f"pothole_{now}.jpg")
                cv2.imwrite(img_path, annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 90])

                record = {
                    "event_time": now,
                    "delta": delta,
                    "gps": gps_data,
                    "detected": detected,
                    "image": img_path
                }

                json_path = os.path.join(SAVE_DIR, f"pothole_{now}.json")
                with open(json_path, "w") as f:
                    json.dump(record, f, indent=2)

                print(f"[+] Event saved: {json_path}")

        except KeyboardInterrupt:
            print("\n[INFO] Exiting.")
            break
        except Exception as e:
            print("[ERROR]", e)
            time.sleep(1)


if __name__ == "__main__":
    main()
