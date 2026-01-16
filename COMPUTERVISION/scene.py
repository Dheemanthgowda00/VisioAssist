# /home/raspberry/VISIOASSIST/COMPUTERVISION/scene.py

import os
import sys
import time
import cv2
import google.generativeai as genai
import numpy as np
from PIL import Image
from dotenv import load_dotenv
from picamera2 import Picamera2
import sounddevice as sd

# --- Imports for Piper Voice-Over ---
from piper.voice import PiperVoice 
# ----------------------------------------

# Load environment variables from a .env file
load_dotenv()

# --- Configuration ---

# AI Configuration
MODEL_NAME = 'gemini-2.5-flash' 
PROMPT = "Describe what you see in this scene in one concise sentence."

# Camera Configuration
CAMERA_WIDTH, CAMERA_HEIGHT = 640, 480

# Scan Control
NUMBER_OF_SCANS = 2
SCAN_INTERVAL_SECONDS = 5 # Time delay between the two scans

# --- Initialization: API, Camera, and Voice ---

# Load the API key and configure the library
try:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file.")
    genai.configure(api_key=api_key)
except Exception as e:
    print(f"Error initializing Gemini: {e}")
    sys.exit(1)

# Picamera2 Setup
try:
    picam2 = Picamera2()
    # Explicitly set the format to 'BGR888' for OpenCV compatibility
    video_config = picam2.create_video_configuration(
        main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT), "format": 'BGR888'}
    )
    picam2.configure(video_config)
    picam2.start()
    time.sleep(1) # Short warm-up
    print("🚀 Picamera2 initialized.")
except Exception as e:
    print(f"Error initializing Picamera2: {e}")
    sys.exit(1)

# Piper Voice-Over Setup
try:
    # NOTE: Path must be correct for the script's execution environment
    voice = PiperVoice.load("/home/raspberry/VISIOASSIST/VoiceAssistant/assistant/models/piper/en_US-lessac-medium.onnx") 
    print("🎤 Piper voice model loaded successfully.")
except Exception as e:
    print(f"FATAL ERROR: Could not load Piper voice model: {e}")
    sys.exit(1)

# --- Functions ---

def speak_description(text):
    """Converts text to speech using the Piper voice model and plays it."""
    if not text or text.startswith("Error:"):
        return

    try:
        audio_chunks = voice.synthesize(text)
        audio_bytes = b"".join(chunk.audio_int16_bytes for chunk in audio_chunks)
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
        sd.play(audio_array, samplerate=16000) 
        sd.wait()
        print(f"🗣️ Spoke: {text}")
    except Exception as e:
        # In a separate process, we just print the error and continue
        print(f"TTS Playback Error: {e}")

def describe_scene_from_frame(frame, prompt: str) -> str:
    """Generates a description for a video frame using the Gemini Vision model."""
    try:
        # BGR to RGB conversion for PIL/Gemini.
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)

        model = genai.GenerativeModel(MODEL_NAME) 

        response = model.generate_content([prompt, img])

        if response.text:
            return response.text.strip()
        else:
            return "Error: Model did not generate text."

    except Exception as e:
        return f"Error: An unexpected error occurred during API call: {e}"


# --- Main Execution Loop ---

if __name__ == "__main__":
    
    speak_description("Visual scan initiated.")
    previous_description = ""
    
    try:
        for i in range(NUMBER_OF_SCANS):
            
            # 1. Capture frame
            frame = picam2.capture_array()
            
            # 2. Get description
            new_description = describe_scene_from_frame(frame, PROMPT)
            
            print(f"--- Scan {i+1} Result: {new_description}")
            
            # 3. Speak only if the description has changed and is not an error
            if new_description and not new_description.startswith("Error:") and new_description != previous_description:
                speak_description(f"Scan {i+1}: {new_description}")
                previous_description = new_description
            
            # 4. Wait for the interval before the next scan
            if i < NUMBER_OF_SCANS - 1:
                time.sleep(SCAN_INTERVAL_SECONDS)
                
    except Exception as e:
        print(f"An error occurred during the main scan loop: {e}")
        speak_description("An error interrupted the visual scan.")
        
    finally:
        # Clean up resources
        picam2.stop()
        speak_description("Visual scan complete. Exiting script.")
        print("📷 Camera released. Scene description script finished.")
        sys.exit(0)