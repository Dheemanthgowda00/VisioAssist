import os
import sys
import time
import threading
import cv2
import google.generativeai as genai
import json # Explicitly import json for parsing
from PIL import Image
from dotenv import load_dotenv
from flask import Flask, Response, render_template_string
from picamera2 import Picamera2
import numpy as np

# Load environment variables (for GOOGLE_API_KEY)
load_dotenv()

# --- Global State and Configuration ---

# Global variables for communication between threads
latest_detections = "Awaiting first Gemini scan..."
detection_lock = threading.Lock() 
last_api_call_time = time.time()

# API/Model Configuration
MODEL_NAME = 'gemini-2.5-flash' # High-throughput model
CAMERA_WIDTH, CAMERA_HEIGHT = 640, 480
API_CALL_INTERVAL = 15 # seconds (Safe interval to avoid hitting API quotas)

# Prompt to instruct Gemini to act as an object detector and return structured text
GEMINI_DETECTION_PROMPT = (
    "Analyze the image and list all distinct, visible objects. "
    "For each object, estimate its normalized bounding box (X_min, Y_min, X_max, Y_max) "
    "where coordinates range from 0.0 to 1.0. Format the response strictly as a single JSON array "
    "of objects with 'label' and 'box' keys. Example: "
    "[{\"label\": \"cat\", \"box\": [0.1, 0.2, 0.5, 0.6]}, {\"label\": \"sofa\", \"box\": [0.0, 0.7, 1.0, 1.0]}]"
)


# Load the API key and configure the library
try:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file or environment variables.")
    genai.configure(api_key=api_key)
except ValueError as e:
    print(f"Error: {e}")
    sys.exit(1)


# --- Picamera2 Setup ---

try:
    picam2 = Picamera2()
    video_config = picam2.create_video_configuration(
        main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT), "format": 'BGR888'}
    )
    picam2.configure(video_config)
    picam2.start()
    time.sleep(2)
    print("🚀 Picamera2 initialized.")
except Exception as e:
    print(f"Error initializing Picamera2: {e}")
    sys.exit(1)


# --- Background Detection Worker (Gemini Integration) ---

class BackgroundDetectionManager(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.running = True
        
        # **TIMEOUT FIX:** Initialize the model once with the request_options for timeout
        try:
            self.model = genai.GenerativeModel(
                MODEL_NAME,
                request_options={'timeout': 10} # Set the API call timeout to 10 seconds
            )
        except Exception as e:
            print(f"FATAL ERROR: Could not initialize Gemini model: {e}")
            self.running = False
            self.model = None # Ensure model is None if initialization failed

    def run(self):
        global latest_detections
        if not self.running:
            return

        print("🤖 Gemini Detection Background Task started.")
        while self.running:
            try:
                # 1. Capture a frame
                frame = picam2.capture_array()
                
                # 2. Convert OpenCV BGR frame to PIL Image (RGB) for Gemini
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb_frame)

                # 3. Call the Gemini API (Timeout is handled by request_options)
                response = self.model.generate_content([GEMINI_DETECTION_PROMPT, img])

                # 4. Process response (Parse JSON output)
                json_string = response.text.strip()
                
                try:
                    # Attempt to parse the JSON array
                    detections_list = json.loads(json_string)
                    # Simple validation: ensure it's a list
                    if isinstance(detections_list, list) and all('label' in d and 'box' in d for d in detections_list):
                        new_detections = detections_list
                    else:
                        new_detections = [{"label": "Parsing Error: Invalid AI Output", "box": [0, 0, 0, 0]}]
                except json.JSONDecodeError:
                    new_detections = [{"label": f"AI Parsing Failed (Not JSON): {json_string[:30]}...", "box": [0, 0, 0, 0]}]
                
                # 5. Update global state safely
                with detection_lock:
                    latest_detections = new_detections
                    print(f"🔍 Detections found: {len(new_detections)}")

            except Exception as e:
                # This catches the timeout exception or any other API error
                error_msg = f"API Error/Exception (Timeout ❌?): {e}"
                print(f"⚠️ {error_msg}")
                with detection_lock:
                    latest_detections = [{"label": error_msg, "box": [0, 0, 0, 0]}]
            
            # Wait for the next interval
            time.sleep(API_CALL_INTERVAL)

    def stop(self):
        self.running = False


# --- Core Detection and Streaming Logic ---

def draw_boxes_and_encode_frame():
    """Captures a frame, draws bounding boxes, and encodes to JPEG for the stream."""
    try:
        # 1. Capture the latest live frame
        frame = picam2.capture_array()
        
        # 2. Get the latest detection results
        with detection_lock:
            current_detections = latest_detections

        # 3. Process and Draw on the frame
        if isinstance(current_detections, list):
            for item in current_detections:
                label = item.get('label', 'Unknown')
                box_normalized = item.get('box') # [xmin, ymin, xmax, ymax] (0.0 to 1.0)
                
                if box_normalized and len(box_normalized) == 4:
                    # Convert normalized coordinates (0-1) to pixel coordinates (0-640/480)
                    h, w, _ = frame.shape
                    
                    x1 = int(box_normalized[0] * w)
                    y1 = int(box_normalized[1] * h)
                    x2 = int(box_normalized[2] * w)
                    y2 = int(box_normalized[3] * h)
                    
                    if x1 < x2 and y1 < y2:
                        # Draw box (BGR Blue)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                        
                        # Draw label
                        text = f"{label}"
                        cv2.putText(frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                                    0.7, (255, 255, 255), 2) # BGR White text

        # 4. **COLOR CORRECTION & ENCODE:** Convert BGR -> RGB for web display
        frame_rgb_display = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        ret, buffer = cv2.imencode('.jpg', frame_rgb_display, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        return buffer.tobytes()

    except Exception as e:
        # Log the exception for the stream process
        # print(f"Error during frame streaming: {e}") 
        return None

def gen_frames():
    """Motion JPEG stream generator."""
    while True:
        frame_bytes = draw_boxes_and_encode_frame()
        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.01)

# --- Flask Application Setup (HTML and Routing) ---
app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Pi Gemini Object Stream</title>
    <style>
        body { text-align: center; font-family: Arial, sans-serif; background-color: #1a1a1a; color: #f0f0f0; }
        h1 { color: #00bcd4; margin-bottom: 20px; }
        .container { display: flex; justify-content: center; align-items: flex-start; gap: 40px; margin-top: 20px;}
        .description-box { 
            width: 350px; 
            padding: 20px; 
            border: 2px solid #00bcd4; 
            border-radius: 12px; 
            text-align: left; 
            background-color: #2c2c2c; 
            box-shadow: 0 4px 15px rgba(0, 188, 212, 0.3);
        }
        .description-box h2 { margin-top: 0; color: #ffeb3b; font-size: 1.4em; }
        .description-box p { font-size: 1.1em; word-wrap: break-word; }
        img { border: 4px solid #444; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.5); }
    </style>
</head>
<body>
    <h1>Live Raspberry Pi Gemini Object Detection</h1>
    <div class="container">
        <img src="{{ url_for('video_feed') }}" width="640" height="480">
        <div class="description-box">
            <h2>Latest Detections ({{ model_name }}):</h2>
            <p id="description">{{ current_description }}</p>
            <p style="font-size: 0.9em; color: #999;">Scanning frequency: {{ api_interval }} seconds.</p>
        </div>
    </div>
    <script>
        function updateDetections() {
            fetch('/detection_feed')
                .then(response => response.json())
                .then(data => {
                    let text = "Awaiting first Gemini scan...";
                    
                    if (Array.isArray(data) && data.length > 0) {
                        if (data[0].label && data[0].label.includes('API Error') || data[0].label.includes('Parsing Failed')) {
                             text = data[0].label; // Display the error message
                        } else {
                            text = data.map(item => item.label).join(', '); // Display object labels
                        }
                    } 
                    document.getElementById('description').innerText = text;
                })
                .catch(error => {
                    document.getElementById('description').innerText = 'Web Connection Error.';
                });
        }
        setInterval(updateDetections, 1000); 
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Renders the main web page."""
    with detection_lock:
        # Pass JSON data as a string initially
        current_description = latest_detections if isinstance(latest_detections, str) else ", ".join(d['label'] for d in latest_detections if 'label' in d)

    return render_template_string(HTML_PAGE, 
                                  current_description=current_description,
                                  api_interval=API_CALL_INTERVAL,
                                  model_name=MODEL_NAME)

@app.route('/video_feed')
def video_feed():
    """Route to serve the streaming video (MJPEG)."""
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/detection_feed')
def detection_feed():
    """Simple route to provide the latest detections as JSON or status string."""
    with detection_lock:
        # Return the actual JSON list for the frontend JS to parse and display labels
        if isinstance(latest_detections, list):
            return json.dumps(latest_detections)
        else:
            # Handle the initial status string or error string case
            return json.dumps([{"label": latest_detections, "box": [0, 0, 0, 0]}])


# --- Script Execution ---

if __name__ == '__main__':
    # Initialize the global detection list to ensure it's a list for drawing
    with detection_lock:
        # Note: Set to a descriptive string initially, which JS handles
        latest_detections = "Awaiting first Gemini scan..." 

    # Start the detection worker thread
    detection_manager = BackgroundDetectionManager()
    detection_manager.start()

    print(f"PiCamera is running. Access the web stream at http://<Your_Pi_IP_Address>:5000")
    print(f"Gemini API will be called every {API_CALL_INTERVAL} seconds using {MODEL_NAME}.")
    
    try:
        # Start the Flask web server
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped manually.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        # Ensure the background thread and camera are stopped cleanly
        detection_manager.stop()
        detection_manager.join()
        picam2.stop()
        print("📷 Camera and Gemini Detection manager released.")