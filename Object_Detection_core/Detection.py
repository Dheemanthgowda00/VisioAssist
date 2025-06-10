import cv2
import subprocess
import threading

# Load class names
classNames = []
classFile = r'/home/raspberry/VisioAssist_Final/object_detection/coco.names'
with open(classFile, 'rt') as f:
    classNames = f.read().rstrip('\n').split('\n')

configPath = r'/home/raspberry/VisioAssist_Final/object_detection/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt'
weightsPath = r'/home/raspberry/VisioAssist_Final/object_detection/frozen_inference_graph.pb'

# Initialize the network model
net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

# Initialize the camera
cap = cv2.VideoCapture(0)
cap.set(3, 640)  # Set width
cap.set(4, 480)  # Set height

# Function to use eSpeak for speech output
def speak(text):
    subprocess.run(f'espeak "{text}"', shell=True)

# Real-time detection without displaying the video stream
while True:
    ret, frame = cap.read()

    if not ret:
        print("Failed to capture frame.")
        break

    # Detect objects in the frame
    classIds, confs, bbox = net.detect(frame, confThreshold=0.55)

    if len(classIds) != 0:
        for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
            className = classNames[classId - 1].upper()  # Get the object name
            confidence_text = f"Confidence: {round(confidence * 100, 2)}%"  # Optional to show confidence level

            # Speak the detected object name
            speak(f"Detected {className}")

# Release the camera when done
cap.release()
