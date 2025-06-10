# from ultralytics import YOLO

# model = YOLO('/home/raspberry/VisioAssist_Final/FireDetection_core/best.pt')
# model.predict(source = 0, imgsz=720 , conf=0.7)

import os
import time
from ultralytics import YOLO

model = YOLO('/home/raspberry/VisioAssist_Final/FireDetection_core/best.pt')

def speak(text):
    os.system(f'espeak "{text}"')

prev_detection = None
prev_time = time.time()

for result in model.predict(source=0, imgsz=720, conf=0.5, stream=True):
    detections = result.boxes

    if detections:
        for box in detections:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            class_name = result.names[class_id]

            # Check if the current detection is the same as the previous one to reduce repetitive output
            if (class_name != prev_detection) or (time.time() - prev_time > 2):
                print(f"Detected: {class_name} with confidence {confidence:.2%}")
                speak(f"Detected {class_name}")
                prev_detection = class_name
                prev_time = time.time()

    else:
        if (prev_detection != "no detection") or (time.time() - prev_time > 2):
            print("No detections")
            speak("No detections")
            prev_detection = "no detection"
            prev_time = time.time()
