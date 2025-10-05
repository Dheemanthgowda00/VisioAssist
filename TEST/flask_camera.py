import time
import cv2
import numpy as np
from picamera2 import Picamera2
from flask import Flask, Response, render_template_string

# --- HTML Template String ---
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Raspberry Pi Camera Stream</title>
    <style>
        /* Basic styling to center the video */
        body { 
            text-align: center; 
            font-family: Arial, sans-serif;
        }
        h1 { 
            color: #333; 
        }
        img {
            border: 3px solid #555;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <h1>Live Camera Feed (Camera Module 3 Wide)</h1>
    <img src="{{ url_for('video_feed') }}" width="640" height="480">
</body>
</html>
"""

# --- Camera Stream Generator Class ---
class CameraStream:
    def __init__(self):
        # Initialize Picamera2
        self.picam2 = Picamera2()
        
        # Configure for video (smaller size for faster streaming)
        self.config = self.picam2.create_video_configuration(main={"size": (640, 480)})
        self.picam2.configure(self.config)
        self.picam2.start()
        
        # Allow the camera to warm up
        time.sleep(2)

    def get_frame(self):
        # Capture an array from the camera (Picamera2 often returns BGR)
        frame_array = self.picam2.capture_array()
        
        # --- FIX: CONVERT BGR TO RGB FOR PROPER COLORS ---
        # OpenCV's cv2.imencode expects the color array to be in the correct order.
        # We explicitly convert the BGR array to RGB.
        frame_array = cv2.cvtColor(frame_array, cv2.COLOR_BGR2RGB)
        # ------------------------------------------------
        
        # OpenCV encodes the array to JPEG bytes for the stream
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90] 
        ret, buffer = cv2.imencode('.jpg', frame_array, encode_param)
        
        return buffer.tobytes()

# --- Flask Application Setup ---
app = Flask(__name__)
camera = CameraStream()

@app.route('/')
def index():
    """Video streaming home page, renders the embedded HTML string."""
    return render_template_string(HTML_PAGE)

def gen_frames():
    """Video streaming generator function (Motion JPEG format)."""
    while True:
        frame = camera.get_frame()
        # Yield the frame in the Motion JPEG format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    """Route to serve the streaming video."""
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# --- Run the App ---
if __name__ == '__main__':
    # '0.0.0.0' makes the server accessible from other devices on the network.
    # use_reloader=False is crucial to prevent the "Device or resource busy" error.
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)