import os
import sys
import time
import threading
import cv2
# Import Gemini components for the background task
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv 
from flask import Flask, Response, render_template_string
from picamera2 import Picamera2
import numpy as np

# Load environment variables (for GOOGLE_API_KEY)
load_dotenv()

# --- Global State and Configuration ---

latest_ocr_text = "Awaiting first Gemini OCR scan..."
ocr_lock = threading.Lock() 

# --- Gemini API Configuration ---
# We will use the fast model for this type of repeated vision task
MODEL_NAME = 'gemini-2.5-flash' 
# Instruction prompt to make Gemini act as an OCR system
GEMINI_OCR_PROMPT = (
    "Analyze the image content. Transcribe ALL text you see clearly and accurately. "
    "If no clear text is visible, respond ONLY with 'No readable text was detected.'"
)

# Camera configuration
CAMERA_WIDTH, CAMERA_HEIGHT = 640, 480
FRAME_INTERVAL = 4 # seconds between API calls

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


# --- Background OCR Worker (Gemini Integration) ---

class BackgroundTaskManager(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.running = True

    def run(self):
        global latest_ocr_text
        print("🤖 Gemini OCR Background Task started.")
        while self.running:
            try:
                # 1. Capture a frame
                frame = picam2.capture_array()
                
                # 2. Convert OpenCV BGR frame to PIL Image (RGB) for Gemini
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb_frame)

                # 3. Call the Gemini API
                model = genai.GenerativeModel(MODEL_NAME)
                response = model.generate_content([GEMINI_OCR_PROMPT, img])

                # 4. Process response
                extracted_text = response.text.strip()
                
                if not extracted_text or "no readable text was detected" in extracted_text.lower():
                    extracted_text = "No readable text was detected."
                else:
                    # Clean up newlines and extra spaces for display
                    extracted_text = " ".join(extracted_text.split())

                # 5. Update global state safely
                with ocr_lock:
                    latest_ocr_text = extracted_text
                    print(f"🔍 OCR Result: {extracted_text[:60]}...")

            except Exception as e:
                error_msg = f"API Error: Check quota/model access: {e}"
                print(f"⚠️ {error_msg}")
                with ocr_lock:
                    latest_ocr_text = error_msg
            
            # Wait for the next interval
            time.sleep(FRAME_INTERVAL)

    def stop(self):
        self.running = False


# --- Flask Streaming Logic ---

app = Flask(__name__)

def gen_frames():
    """Generates the Motion JPEG stream from the camera."""
    while True:
        # 1. Capture frame
        frame = picam2.capture_array()
        
        # 2. Get the latest OCR text for overlay
        with ocr_lock:
            current_ocr_text = latest_ocr_text
            
        # 3. Add OCR text overlay to the frame
        overlay_text = f"OCR: {current_ocr_text[:50]}..."
        cv2.putText(frame, overlay_text, (10, CAMERA_HEIGHT - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2) # Yellow color for text
        
        # 4. **COLOR CORRECTION & ENCODE:** Convert BGR -> RGB for web display
        frame_rgb_display = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        ret, buffer = cv2.imencode('.jpg', frame_rgb_display)
        frame_bytes = buffer.tobytes()

        # 5. Yield the frame in MJPEG format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Stream speed control
        time.sleep(0.01)


# --- Flask Application Setup (HTML and Routing) ---

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Pi Gemini OCR Stream</title>
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
    <h1>Live Raspberry Pi Gemini OCR Scanner</h1>
    <div class="container">
        <img src="{{ url_for('video_feed') }}" width="{{ cam_w }}" height="{{ cam_h }}">
        <div class="description-box">
            <h2>Latest Recognized Text:</h2>
            <p id="description">{{ current_description }}</p>
            <p style="font-size: 0.9em; color: #999;">Scanning frequency: {{ frame_interval }} seconds.</p>
        </div>
    </div>
    <script>
        function updateDescription() {
            fetch('/text_feed')
                .then(response => response.text())
                .then(text => {
                    document.getElementById('description').innerText = text;
                })
                .catch(error => {
                    document.getElementById('description').innerText = 'Connection Error.';
                });
        }
        setInterval(updateDescription, 1000); 
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Renders the main web page."""
    with ocr_lock:
        current_description = latest_ocr_text

    return render_template_string(HTML_PAGE, 
                                  current_description=current_description,
                                  frame_interval=FRAME_INTERVAL,
                                  cam_w=CAMERA_WIDTH,
                                  cam_h=CAMERA_HEIGHT)

@app.route('/video_feed')
def video_feed():
    """Route to serve the streaming video (MJPEG)."""
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/text_feed')
def text_feed():
    """Simple route to provide the latest OCR description as plain text."""
    with ocr_lock:
        return latest_ocr_text


# --- Script Execution ---

if __name__ == "__main__":
    # Start the OCR worker thread
    ocr_manager = BackgroundTaskManager()
    ocr_manager.start()

    print(f"PiCamera is running. Access the web stream at http://<Your_Pi_IP_Address>:5000")
    print(f"Gemini API will be called every {FRAME_INTERVAL} seconds.")
    
    try:
        # Start the Flask web server
        app.run(host='0.0.0.0', port=5003, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped manually.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        # Ensure the background thread and camera are stopped cleanly
        ocr_manager.stop()
        ocr_manager.join()
        picam2.stop()
        print("📷 Camera and Gemini OCR manager released.")