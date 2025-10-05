import os
import sys
import time
import cv2
import google.generativeai as genai
import numpy as np
from PIL import Image
from dotenv import load_dotenv
from flask import Flask, Response, render_template_string
from picamera2 import Picamera2
import sounddevice as sd

# --- New Imports for Piper Voice-Over ---
# NOTE: Ensure the 'piper' library is installed (pip install piper-tts)
from piper.voice import PiperVoice 
# ----------------------------------------

# Load environment variables from a .env file
load_dotenv()

# --- Global State and Configuration ---

# Global variable to store the latest AI description for web rendering
latest_ai_description = "Awaiting first AI analysis..."
# New global variable to store the *previous* description for change detection
previous_ai_description = ""
# Time tracking to control how often the expensive API call is made
last_api_call_time = time.time()

# AI call interval (15 seconds to avoid exceeding API limits)
API_CALL_INTERVAL = 15 # seconds 

# Camera configuration
CAMERA_WIDTH, CAMERA_HEIGHT = 640, 480
PROMPT = "Describe what you see in this scene in one sentence."

# Model configuration
MODEL_NAME = 'gemini-2.5-flash' 

# Load the API key and configure the library
try:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file or environment variables.")
    genai.configure(api_key=api_key)
except ValueError as e:
    print(f"Error: {e}")
    print("Please make sure you have a .env file with your GOOGLE_API_KEY.")
    sys.exit(1)


# --- Picamera2 Setup ---

try:
    picam2 = Picamera2()
    # Explicitly set the format to 'BGR888' (3-channel BGR) for OpenCV compatibility
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


# --- Piper Voice-Over Setup and Function ---

try:
    # Load the specific voice model
    voice = PiperVoice.load("VoiceAssistant/assistant/models/piper/en_US-lessac-medium.onnx") 
    print("🎤 Piper voice model loaded successfully.")
except Exception as e:
    print(f"\nFATAL ERROR: Could not load Piper voice model. Check path and dependencies: {e}")
    # Exit if the voice model cannot be loaded, as TTS is a core feature now.
    sys.exit(1)

def speak_description(text):
    """
    Converts text to speech using the Piper voice model.
    """
    if not text or text.startswith("Error:"):
        return

    try:
        # Synthesize the audio
        audio_chunks = voice.synthesize(text)
        
        # Combine chunks into a single audio array
        audio_bytes = b"".join(chunk.audio_int16_bytes for chunk in audio_chunks)
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
        
        # Play the audio (Piper models typically use 16000 Hz)
        sd.play(audio_array, samplerate=16000) 
        sd.wait()
        print(f"🗣️ Spoke: {text}")

    except Exception as e:
        print(f"TTS Playback Error: {e}")


# --- AI Function ---

def describe_scene_from_frame(frame, prompt: str) -> str:
    """
    Generates a description for a video frame using the Gemini Vision model.
    """
    global latest_ai_description
    
    try:
        # The frame is BGR from Picamera2. Convert to RGB for PIL/Gemini.
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)

        model = genai.GenerativeModel(MODEL_NAME) 

        response = model.generate_content([prompt, img])

        if response.text:
            description = response.text.strip()
            latest_ai_description = description
            return description
        else:
            return "Error: Model did not generate text."

    except Exception as e:
        error_msg = f"An unexpected error occurred during API call: {e}"
        latest_ai_description = error_msg
        return error_msg


# --- Flask Streaming Logic ---

app = Flask(__name__)

def gen_frames():
    """Generates frames for the Motion JPEG stream."""
    global last_api_call_time, latest_ai_description, previous_ai_description

    while True:
        # 1. Capture frame from Picamera2
        frame = picam2.capture_array()
        
        # 2. Check if it's time to call the API
        current_time = time.time()
        if current_time - last_api_call_time > API_CALL_INTERVAL:
            last_api_call_time = current_time
            
            # --- Call AI and Handle Voice-Over ---
            new_description = describe_scene_from_frame(frame, PROMPT)
            
            if new_description and new_description != previous_ai_description and not new_description.startswith("Error:"):
                # Speak the new description and update the previous state
                speak_description(new_description)
                previous_ai_description = new_description
            # --------------------------------------
            
            print(f"🎨 New Description: {latest_ai_description}")
            
        # 3. Add AI Description text overlay to the frame
        overlay_text = f"AI: {latest_ai_description[:50]}..."
        cv2.putText(frame, overlay_text, (10, CAMERA_HEIGHT - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # 4. COLOR FIX & ENCODE: Convert the drawn-upon BGR frame to JPEG bytes.
        frame_rgb_display = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        ret, buffer = cv2.imencode('.jpg', frame_rgb_display) 
        frame_bytes = buffer.tobytes()

        # 5. Yield the frame in MJPEG format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.01) # Control frame rate


# --- Flask Application Setup (HTML and Routing) ---

# HTML Template to display video and description 
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Gemini Vision Pi Stream</title>
    <style>
        body { text-align: center; font-family: Arial, sans-serif; }
        h1 { color: #333; }
        .container { display: flex; justify-content: center; align-items: flex-start; gap: 30px; margin-top: 20px;}
        .description-box { width: 300px; padding: 15px; border: 1px solid #ccc; border-radius: 8px; text-align: left; background-color: #f8f8f8; }
        .description-box h2 { margin-top: 0; color: #007bff; }
        img { border: 3px solid #555; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Live Gemini Vision Stream (Raspberry Pi)</h1>
    <div class="container">
        <img src="{{ url_for('video_feed') }}" width="{{ cam_w }}" height="{{ cam_h }}">
        <div class="description-box">
            <h2>Latest AI Description:</h2>
            <p id="description">{{ current_description }}</p>
            <p style="font-size: 0.8em; color: #666;">AI call interval: {{ api_interval }} seconds.</p>
        </div>
    </div>
    <script>
        function updateDescription() {
            fetch('/description_feed')
                .then(response => response.text())
                .then(text => {
                    document.getElementById('description').innerText = text;
                });
        }
        setInterval(updateDescription, 1000); 
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE, 
                                  current_description=latest_ai_description,
                                  api_interval=API_CALL_INTERVAL,
                                  cam_w=CAMERA_WIDTH,
                                  cam_h=CAMERA_HEIGHT)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/description_feed')
def description_feed():
    return latest_ai_description


# --- Script Execution ---

if __name__ == "__main__":
    print(f"PiCamera is running. Access the web stream at http://<Your_Pi_IP_Address>:5002")
    print(f"AI will be called every {API_CALL_INTERVAL} seconds and **spoken** aloud using Piper.")
    
    try:
        # Note: debug=True and use_reloader=False are often used together for embedded systems
        app.run(host='0.0.0.0', port=5002, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped manually.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        picam2.stop()
        print("📷 Camera released.")