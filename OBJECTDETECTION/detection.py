import cv2
import time
import numpy as np
import io
from picamera2 import Picamera2
from flask import Flask, Response, render_template_string

# --- Configuration & Initialization ---

# ───── HTML Template String ─────
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Web Stream Object Detection</title>
    <style>
        body { text-align: center; font-family: Arial, sans-serif; }
        h1 { color: #333; }
        img { border: 3px solid #555; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Live Object Detection Stream</h1>
    <img src="{{ url_for('video_feed') }}" width="640" height="480">
</body>
</html>
"""

# ───── Paths ─────
classFile = r'/home/raspberry/VISIOASSIST/OBJECTDETECTION/coco.names'
configPath = r'/home/raspberry/VISIOASSIST/OBJECTDETECTION/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt'
weightsPath = r'/home/raspberry/VISIOASSIST/OBJECTDETECTION/frozen_inference_graph.pb'

# ───── Parameters ─────
CAMERA_WIDTH, CAMERA_HEIGHT = 640, 480
CONFIDENCE_THRESHOLD = 0.55
FONT_SCALE = 2
FONT_THICKNESS = 2
BOX_COLOR = (255, 0, 0) # BGR Blue

# ───── Load class names ─────
classNames = []
try:
    with open(classFile, 'rt') as f:
        classNames = f.read().rstrip('\n').split('\n')
except FileNotFoundError:
    print(f"ERROR: Class file not found at {classFile}")
    exit()

# ───── Initialize model ─────
try:
    net = cv2.dnn_DetectionModel(weightsPath, configPath)
    net.setInputSize(320, 320)
    net.setInputScale(1.0 / 127.5)
    net.setInputMean((127.5, 127.5, 127.5))
    net.setInputSwapRB(True)
except Exception as e:
    print(f"ERROR initializing DNN model: {e}")
    exit()

# ───── Initialize Camera ─────
picam2 = Picamera2()

# **DNN Fix (Input Channels):** Explicitly set format to 'BGR888' (3-channel BGR) 
video_config = picam2.create_video_configuration(
    main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT), "format": 'BGR888'} 
)
picam2.configure(video_config)
picam2.start()
time.sleep(2)
print("🚀 Picamera2 and Object Detection Model initialized.")


# --- Core Detection and Streaming Logic ---

def process_and_encode_frame():
    """Captures a frame, runs detection, draws boxes, and encodes to JPEG."""
    try:
        # 1. Capture frame (is 3-channel BGR)
        frame = picam2.capture_array()
        
        # 2. Run Object Detection
        classIds, confs, bbox = net.detect(frame, confThreshold=CONFIDENCE_THRESHOLD)

        # 3. Draw detections on the frame
        if len(classIds) != 0:
            for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
                
                x, y, w, h = box[0], box[1], box[2], box[3]
                className = classNames[classId - 1].upper()
                label = f"{className}: {round(confidence * 100, 2)}%"
                
                # Draw box
                cv2.rectangle(frame, (x, y), (x + w, y + h), BOX_COLOR, FONT_THICKNESS)
                
                # Draw label
                cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                            0.7, BOX_COLOR, FONT_THICKNESS)

        # 4. **COLOR FIX:** Convert from BGR (OpenCV) to RGB (Web Browser/JPEG)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 5. Encode the frame to JPEG for streaming
        ret, buffer = cv2.imencode('.jpg', frame_rgb, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        return buffer.tobytes()

    except Exception as e:
        print(f"Error during frame processing: {e}")
        time.sleep(1) 
        return None

def gen_frames():
    """Motion JPEG stream generator."""
    while True:
        frame_bytes = process_and_encode_frame()
        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.01)

# --- Flask Application Setup ---
app = Flask(__name__)

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template_string(HTML_PAGE)

@app.route('/video_feed')
def video_feed():
    """Route to serve the streaming video."""
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# --- Run the App and Cleanup ---
if __name__ == '__main__':
    try:
        # use_reloader=False is mandatory to prevent camera busy error
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped manually.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        picam2.stop()
        print("📷 Camera released.")