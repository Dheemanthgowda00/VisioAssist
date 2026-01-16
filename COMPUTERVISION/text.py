# /home/raspberry/VISIOASSIST/COMPUTERVISION/ocr_reader.py

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
from piper.voice import PiperVoice 

# Load environment variables
load_dotenv()

# --- Configuration ---

MODEL_NAME = 'gemini-2.5-flash' 
# Instruction prompt to make Gemini act as an OCR system
GEMINI_OCR_PROMPT = (
    "Analyze the image content. Transcribe ALL text you see clearly and accurately. "
    "If no clear text is visible, respond ONLY with 'No readable text was detected.'"
)

# Camera Configuration
CAMERA_WIDTH, CAMERA_HEIGHT = 640, 480
FRAME_INTERVAL = 4 # seconds between API calls

# --- Initialization: API, Camera, and Voice ---

# Load API key and configure Gemini
try:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found.")
    genai.configure(api_key=api_key)
except Exception as e:
    print(f"Error initializing Gemini: {e}")
    sys.exit(1)

# Picamera2 Setup
try:
    picam2 = Picamera2()
    video_config = picam2.create_video_configuration(
        main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT), "format": 'BGR888'}
    )
    picam2.configure(video_config)
    picam2.start()
    time.sleep(1)
    print("🚀 Picamera2 initialized for OCR.")
except Exception as e:
    print(f"Error initializing Picamera2: {e}")
    sys.exit(1)

# Piper Voice-Over Setup
try:
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
        print(f"TTS Playback Error: {e}")

def describe_scene_from_frame(frame, prompt: str) -> str:
    """Generates a description/transcription using Gemini Vision model."""
    try:
        # BGR to RGB conversion for PIL/Gemini.
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)

        model = genai.GenerativeModel(MODEL_NAME) 
        response = model.generate_content([prompt, img])

        if response.text:
            # Clean up newlines and extra spaces for display and speech
            return " ".join(response.text.strip().split())
        else:
            return "No text response from model."

    except Exception as e:
        return f"Error: API call failed: {e}"


# --- Main Execution Loop ---

if __name__ == "__main__":
    
    speak_description("Continuous reading mode activated.")
    
    # We will use this flag and the timer in the main assistant to control duration.
    previous_text = "initial state" 
    
    try:
        while True:
            # 1. Capture frame
            frame = picam2.capture_array()
            
            # 2. Get description
            current_text = describe_scene_from_frame(frame, GEMINI_OCR_PROMPT)
            
            print(f"--- OCR Result: {current_text}")
            
            # 3. Speak only if the text has changed and is not a default/error message
            if (current_text.lower() != previous_text.lower() and 
                "no readable text was detected" not in current_text.lower() and
                "error:" not in current_text.lower()):
                
                speak_description(f"I read: {current_text}")
                previous_text = current_text
            
            # 4. Wait for the interval before the next scan
            time.sleep(FRAME_INTERVAL)
                
    except Exception as e:
        print(f"An error occurred during the main OCR loop: {e}")
        # The main assistant will kill this process, so we don't need a clean exit speak.
        
    finally:
        # Clean up resources
        picam2.stop()
        print("📷 Camera released. OCR reader script finished.")
        sys.exit(0)