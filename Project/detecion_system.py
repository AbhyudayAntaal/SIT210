import serial
import numpy as np
import cv2
import time
import os
import subprocess
import json
from datetime import datetime
from gps3 import gps3

SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600
SAVE_DIR = 'pothole_images'
GPS_LOG_FILE = 'pothole_gps_log.json'
POTHOLE_THRESHOLD = 0.6
UNCERTAIN_THRESHOLD = 0.4
TEMP_IMAGE = '/tmp/capture.jpg'

os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(f"{SAVE_DIR}/potholes", exist_ok=True)
os.makedirs(f"{SAVE_DIR}/uncertain", exist_ok=True)
os.makedirs(f"{SAVE_DIR}/non_potholes", exist_ok=True)

class GPSModule:
    def __init__(self):
        try:
            self.gps_socket = gps3.GPSDSocket()
            self.data_stream = gps3.DataStream()
            self.gps_socket.connect()
            self.gps_socket.watch()
            self.enabled = True
            print("GPS module initialized successfully!")
            time.sleep(1)
        except Exception as e:
            print(f"GPS initialization failed: {e}")
            print("Continuing without GPS...")
            self.enabled = False
    
    def get_current_location(self):
        if not self.enabled:
            return None
        
        try:
            for _ in range(10):
                new_data = self.gps_socket.next(timeout=1)
                if new_data:
                    self.data_stream.unpack(new_data)
                    
                    lat = self.data_stream.TPV['lat']
                    lon = self.data_stream.TPV['lon']
                    alt = self.data_stream.TPV['alt']
                    speed = self.data_stream.TPV['speed']
                    
                    if lat != 'n/a' and lon != 'n/a':
                        return {
                            'latitude': float(lat),
                            'longitude': float(lon),
                            'altitude': float(alt) if alt != 'n/a' else None,
                            'speed': float(speed) if speed != 'n/a' else None,
                            'timestamp': datetime.now().isoformat()
                        }
            
            return None
            
        except Exception as e:
            print(f"GPS read error: {e}")
            return None
    
    def cleanup(self):
        if self.enabled:
            try:
                self.gps_socket.close()
            except:
                pass

class PotholeDetector:
    def __init__(self):
        print("Camera initialized successfully!")
        
    def capture_image(self):
        try:
            subprocess.run([
                'rpicam-still',
                '-o', TEMP_IMAGE,
                '--immediate',
                '--nopreview',
                '--width', '1920',
                '--height', '1080',
                '--timeout', '1'
            ], check=True, capture_output=True)
            
            frame = cv2.imread(TEMP_IMAGE)
            
            if frame is None:
                print("Error: Failed to read captured image")
                return None
                
            return frame
            
        except subprocess.CalledProcessError as e:
            print(f"Error capturing image: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
    
    def preprocess_image(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        return gray, blurred
    
    def detect_pothole(self, image):
        gray, blurred = self.preprocess_image(image)
        annotated = image.copy()
        
        edges = cv2.Canny(blurred, 50, 150)
        
        adaptive_thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        combined = cv2.bitwise_or(edges, adaptive_thresh)
        
        kernel = np.ones((5, 5), np.uint8)
        morphed = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)
        morphed = cv2.morphologyEx(morphed, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(
            morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        pothole_features = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            if area < 500 or area > 50000:
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h if h > 0 else 0
            
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            
            mask = np.zeros(gray.shape, dtype=np.uint8)
            cv2.drawContours(mask, [contour], -1, 255, -1)
            mean_intensity = cv2.mean(gray, mask=mask)[0]
            
            score = 0
            
            if mean_intensity < 100:
                score += 0.3
            
            if 0.4 < aspect_ratio < 2.5:
                score += 0.2
            
            if 0.3 < circularity < 0.8:
                score += 0.3
            
            if 1000 < area < 30000:
                score += 0.2
            
            if score > 0.5:
                pothole_features.append({
                    'contour': contour,
                    'score': score,
                    'bbox': (x, y, w, h),
                    'area': area
                })
                
                cv2.drawContours(annotated, [contour], -1, (0, 255, 0), 2)
                cv2.rectangle(annotated, (x, y), (x+w, y+h), (0, 0, 255), 2)
                cv2.putText(annotated, f"Score: {score:.2f}", (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        if len(pothole_features) > 0:
            best_detection = max(pothole_features, key=lambda x: x['score'])
            confidence = best_detection['score']
            
            if confidence >= POTHOLE_THRESHOLD:
                classification = "pothole"
            elif confidence >= UNCERTAIN_THRESHOLD:
                classification = "uncertain"
            else:
                classification = "non_pothole"
        else:
            classification = "non_pothole"
            confidence = 0.0
        
        return classification, confidence, annotated
    
    def save_image(self, image, annotated, classification, confidence):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        subfolder = classification + "s" if classification == "pothole" else classification
        
        orig_path = f"{SAVE_DIR}/{subfolder}/orig_{timestamp}.jpg"
        cv2.imwrite(orig_path, image)
        
        return orig_path
        
    def cleanup(self):
        if os.path.exists(TEMP_IMAGE):
            os.remove(TEMP_IMAGE)
        print("Cleanup complete")

def save_gps_log(classification, confidence, gps_data, image_path, vibration_magnitude):
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'classification': classification,
        'confidence': confidence,
        'vibration_magnitude': vibration_magnitude,
        'gps': gps_data,
        'image_path': image_path
    }
    
    logs = []
    if os.path.exists(GPS_LOG_FILE):
        try:
            with open(GPS_LOG_FILE, 'r') as f:
                logs = json.load(f)
        except:
            logs = []
    
    logs.append(log_entry)
    
    with open(GPS_LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)

def main():
    print("Initializing Pothole Detection System...")
    
    detector = PotholeDetector()
    gps_module = GPSModule()
    
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        print(f"Connected to Arduino on {SERIAL_PORT}")
    except Exception as e:
        print(f"Error connecting to Arduino: {e}")
        print("Make sure Arduino is connected and the port is correct")
        print("\nAvailable ports:")
        os.system("ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null")
        detector.cleanup()
        gps_module.cleanup()
        return
    
    print("\nSystem ready! Monitoring for vibrations...")
    print("Press Ctrl+C to exit\n")
    
    detection_count = 0
    pothole_count = 0
    uncertain_count = 0
    
    try:
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                
                if "Sudden vibration detected" in line:
                    vibration_mag = line.split("Magnitude: ")[1].split(" ")[0] if "Magnitude:" in line else "N/A"
                    
                    print(f"\n{'='*60}")
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
                    print(f"VIBRATION DETECTED: {line}")
                    
                    gps_data = gps_module.get_current_location()
                    if gps_data:
                        print(f"GPS: {gps_data['latitude']:.6f}, {gps_data['longitude']:.6f}")
                        if gps_data['speed']:
                            print(f"Speed: {gps_data['speed']:.2f} m/s")
                    else:
                        print("GPS: Location unavailable")
                    
                    print("Capturing image...")
                    
                    image = detector.capture_image()
                    
                    if image is None:
                        print("Failed to capture image, skipping analysis")
                        continue
                    
                    print("Analyzing image...")
                    classification, confidence, annotated = detector.detect_pothole(image)
                    
                    detection_count += 1
                    
                    if classification == "pothole":
                        pothole_count += 1
                        print(f"✓ POTHOLE DETECTED! Confidence: {confidence:.2%}")
                    elif classification == "uncertain":
                        uncertain_count += 1
                        print(f"⚠ UNCERTAIN - Possible road damage. Confidence: {confidence:.2%}")
                    else:
                        print(f"✗ No pothole detected. Confidence: {confidence:.2%}")
                    
                    image_path = detector.save_image(image, annotated, classification, confidence)
                    
                    if classification in ["pothole", "uncertain"]:
                        save_gps_log(classification, confidence, gps_data, image_path, vibration_mag)
                        print(f"Location logged to {GPS_LOG_FILE}")
                    
                    print(f"Total: {detection_count} | Potholes: {pothole_count} | Uncertain: {uncertain_count}")
                    print(f"{'='*60}\n")
                    
                    time.sleep(0.5)
                    
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        print(f"\nSession Summary:")
        print(f"Total vibration events: {detection_count}")
        print(f"Potholes detected: {pothole_count}")
        print(f"Uncertain cases: {uncertain_count}")
        print(f"Non-potholes: {detection_count - pothole_count - uncertain_count}")
        if detection_count > 0:
            print(f"Pothole rate: {pothole_count/detection_count*100:.1f}%")
            print(f"Uncertain rate: {uncertain_count/detection_count*100:.1f}%")
        
    finally:
        ser.close()
        detector.cleanup()
        gps_module.cleanup()
        print("System shutdown complete")

if __name__ == "__main__":
    main()