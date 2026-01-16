import os
import sys
import time
import json
import subprocess
import requests
import sounddevice as sd
import numpy as np
import scipy.signal
# --- Imports for Piper (TTS) and Gemini (STT Logic) ---
from piper.voice import PiperVoice 
import speech_recognition as sr 
# --- New Gemini SDK Import ---
from google import genai
from google.genai import types
import google.generativeai as genaiscene
# ----------------------------
from dotenv import load_dotenv
import datetime
import pytz
from twilio.rest import Client
import smtplib
from email.mime.text import MIMEText
import cv2 
from picamera2 import Picamera2 # Use Picamera2 for Raspberry Pi
from PIL import Image

load_dotenv()

# Twilio credentials
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_WHATSAPP = "whatsapp:+14155238886"  # Twilio sandbox number

twilio_client = Client(TWILIO_SID, TWILIO_AUTH)

# Contact mapping (name to number)
CONTACTS = {
    "deepak": "+918867398549"
}

# --- Configuration and Initialization ---
WAKE_WORD = "jarvis"
USER_DATA_FILE = "user_data.json"

# Set the API Key for the Gemini Client from .env
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
weather_api_key = os.getenv("WEATHER_API_KEY")

# === Initialize Gemini Client ===
if not GEMINI_API_KEY:
    print("FATAL ERROR: GEMINI_API_KEY environment variable not set.")
    sys.exit(1)
try:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"FATAL ERROR: Could not initialize Gemini client: {e}")
    sys.exit(1)
# --------------------------------

STATIC_SYSTEM_INSTRUCTION_BASE = (
    "You are Navis, a helpful and highly intelligent assistant. "
    "Use your internal knowledge and real-time grounding capabilities to answer current events questions accurately. "
    "Reply concisely, in less than 30 words. "
)

# Load User Data
def load_user_data():
    """
    Loads user data, guaranteeing that the 'reminders' and 'memory' keys 
    are initialized, even if the user data file is missing or empty.
    """
    data = {}
    
    # 1. Attempt to load the file
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            # Handle case where file exists but is empty/corrupted
            print(f"WARNING: '{USER_DATA_FILE}' is corrupted or empty. Initializing empty structure.")
            data = {}
    
    # 2. GUARANTEE the presence of the necessary keys
    # This prevents the KeyError: 'memory' when the store_memory function runs.
    if 'reminders' not in data:
        data['reminders'] = []
    if 'memory' not in data:
        data['memory'] = {}
        
    return data

user_data = load_user_data() 

# The save_user_data() function is correctly defined and does not need modification.
def save_user_data():
    """Saves the global user_data dictionary to the JSON file."""
    # NOTE: 'user_data' must be accessible as a global variable.
    try:
        with open(USER_DATA_FILE, "w") as f:
            json.dump(user_data, f, indent=4)
    except Exception as e:
        print(f"ERROR: Could not save user data: {e}")

# --- Piper TTS (Speak Function) ---
try:
    voice = PiperVoice.load("assistant/models/piper/en_US-lessac-medium.onnx") 
except ModuleNotFoundError:
    print("\nFATAL ERROR: The 'piper' TTS library import failed.")
    sys.exit(1)
except Exception as e:
    print(f"\nFATAL ERROR: Could not load Piper voice model: {e}")
    sys.exit(1)

def speak(text):
    """Converts text to speech using Piper."""
    print(f"JARVIS: {text}")
    audio_chunks = voice.synthesize(text)
    audio_bytes = b"".join(chunk.audio_int16_bytes for chunk in audio_chunks)
    audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
    sd.play(audio_array, samplerate=16000) 
    sd.wait()

# === STT (Listen Functions) using SpeechRecognition ===
r = sr.Recognizer()

def recognize_speech(timeout=5, phrase_time_limit=15):
    """Captures and returns user audio as text using Google STT."""
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.5) 
        print("Listening for command...")
        try:
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        except sr.WaitTimeoutError:
            print("No speech detected.")
            return None
    
    try:
        command = r.recognize_google(audio).lower() 
        print(f"User said: {command}")
        return command
    except sr.UnknownValueError:
        print("Sorry, I did not understand that.")
        return None
    except sr.RequestError:
        print("Speech service is unavailable. Check internet.")
        return None

def hotword_listener(hotword="jarvis"):
    """Listens continuously for the wake word."""
    with sr.Microphone() as source:
        r.energy_threshold = 700
        r.adjust_for_ambient_noise(source, duration=0.5)
        print(f"Waiting for wake word '{hotword}'...")
        try:
            audio = r.listen(source, timeout=None)
            trigger = r.recognize_google(audio).lower()
            return hotword in trigger
        except:
            return False


# === Command Handlers (Time/Date/AI) ===

def get_current_time():
    india = pytz.timezone("Asia/Kolkata")
    current_time = datetime.datetime.now(india).strftime("%I:%M %p")
    return f"The current time is {current_time}."

def get_current_date():
    india = pytz.timezone("Asia/Kolkata")
    today = datetime.datetime.now(india).strftime("%A, %d %B %Y")
    return f"Today is {today}."

def get_bangalore_weather():
    url = f"http://api.openweathermap.org/data/2.5/weather?q=Bangalore,IN&units=metric&appid={weather_api_key}"
    try:
        response = requests.get(url)
        data = response.json()
        if data["cod"] == 200:
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            return f"The weather in Bangalore is {desc} with a temperature of {temp}°C."
        else:
            return "Sorry, I couldn't fetch the weather right now."
    except Exception as e:
        print(f"Weather API Error: {e}")
        return "There was an error retrieving the weather."
    
def send_email(subject, body, to_email):
    try:
        from_email = "bdheemanth00@gmail.com"
        password = "eeseihkpbxqesqfm"

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(from_email, password)
        server.send_message(msg)
        server.quit()
        speak("Email sent successfully.")
    except Exception as e:
        print(f"Email Error: {e}")
        speak("Failed to send the email.")

def send_whatsapp_message(contact_name, message):
    try:
        if contact_name.lower() not in CONTACTS:
            speak(f"I don't have a contact saved for {contact_name}.")
            return

        to_number = f"whatsapp:{CONTACTS[contact_name.lower()]}"
        msg = twilio_client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP,
            to=to_number
        )
        speak(f"Message sent to {contact_name} on WhatsApp.")
    except Exception as e:
        print(f"Twilio Error: {e}")
        speak("Failed to send the WhatsApp message.")

# === Ask AI Assistant (Gemini 2.5 Flash - DIRECT API) ===
# === Ask AI Assistant (Gemini 2.5 Flash - MODIFIED) ===
def ask_jarvis(prompt):
    """
    Sends prompt to Gemini 2.5 Flash with live date and user memory context.
    """
    
    # 1. Gather Dynamic Context (Current Time and Memory Facts)
    india = pytz.timezone("Asia/Kolkata")
    current_time_date = datetime.datetime.now(india).strftime("%A, %d %B %Y, %I:%M %p %Z")
    
    # Format stored memory into a string
    memory_context = ""
    if user_data.get('memory'):
        fact_list = [f"{key.replace('_', ' ')}: {value}" for key, value in user_data['memory'].items()]
        # Add a clear heading for the facts
        memory_context = "Your personal facts: " + ", ".join(fact_list) + ". "

    # 2. Construct Final System Instruction
    # We combine the static base, the real-time info, and the memory facts.
    final_system_instruction = (
        STATIC_SYSTEM_INSTRUCTION_BASE + 
        f"The current date and time is {current_time_date}. " +
        memory_context + 
        "Use the personal facts provided to answer questions about the user whenever relevant."
    )

    # 3. Call the Gemini API
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt],
            config=types.GenerateContentConfig(
                system_instruction=final_system_instruction # Use the combined instruction
            )
        )
        return response.text.strip()
    except Exception as e:
        print(f"Error during Gemini API call: {e}")
        return "I had trouble connecting to the Gemini service. Please check your network and API key."

# === New Command Handler: Run External Scene Description Script ===

def run_scene_description(duration_seconds=50):
    """
    Starts the full scene description script (scene.py) in a separate process,
    lets it run for a specified duration, and then terminates it.
    
    The scene.py script will handle camera capture, Gemini vision, and TTS voice-over
    during this period.
    """
    
    # 1. Define the path to the scene script
    SCENE_SCRIPT_PATH = "/home/raspberry/VISIOASSIST/COMPUTERVISION/scene.py"
    
    # Check if the file exists before trying to run it
    if not os.path.exists(SCENE_SCRIPT_PATH):
        speak(f"Error: The scene description script was not found at {SCENE_SCRIPT_PATH}.")
        return

    speak(f"Activating visual scene description mode for {duration_seconds} seconds. Please listen carefully for the descriptions.")
    
    try:
        # 2. Start the process
        # Use sys.executable to ensure the script runs with the correct Python environment
        process = subprocess.Popen([sys.executable, SCENE_SCRIPT_PATH])
        
        # 3. Wait for the specified duration while the visual assistant does its job
        time.sleep(duration_seconds)
        
        # 4. Terminate the process gently
        process.terminate()
        
        # 5. Wait for the process to stop, with a small timeout
        try:
            process.wait(timeout=2)
            speak("Scene description completed and visual assistant stopped.")
        except subprocess.TimeoutExpired:
            # If termination fails, forcibly kill the process
            process.kill()
            speak("Scene description process was forcibly stopped.")
            
    except Exception as e:
        print(f"Error starting/stopping scene description process: {e}")
        speak("There was an error trying to run the scene description script.")

# === New Command Handler: Run External OCR Scanner Script ===

def run_ocr_scan(duration_seconds=45):
    """
    Starts the continuous OCR scanning script (ocr_stream.py) in a separate process,
    lets it run for a specified duration, and then terminates it.
    
    The ocr_stream.py script starts a background thread and a Flask web server,
    which is where the actual OCR and live text updating occurs.
    """
    
    # 1. Define the path to the OCR script (assuming you name the file ocr_stream.py)
    # NOTE: You may need to adjust this path based on where you save the provided code.
    OCR_SCRIPT_PATH = "/home/raspberry/VISIOASSIST/COMPUTERVISION/text.py" 
    
    # Check if the file exists before trying to run it
    if not os.path.exists(OCR_SCRIPT_PATH):
        speak(f"Error: The OCR scanner script was not found at {OCR_SCRIPT_PATH}.")
        return

    speak(f"Activating continuous text scanning mode for {duration_seconds} seconds. Please point the camera towards the text you wish to read.")
    
    # Also inform the user where they can view the live output
    speak("The live stream is available at your device's IP address on port five thousand and three.")
    
    try:
        # 2. Start the process
        # Use sys.executable to ensure the script runs with the correct Python environment
        # IMPORTANT: Ensure the provided OCR code is saved as 'ocr_stream.py' in the correct path.
        process = subprocess.Popen([sys.executable, OCR_SCRIPT_PATH])
        
        # 3. Wait for the specified duration while the OCR scanner does its job
        time.sleep(duration_seconds)
        
        # 4. Terminate the process gently
        process.terminate()
        
        # 5. Wait for the process to stop, with a small timeout
        try:
            process.wait(timeout=3)
            speak("Continuous text scanning mode stopped.")
        except subprocess.TimeoutExpired:
            # If termination fails, forcibly kill the process
            process.kill()
            speak("The text scanning process was forcibly stopped.")
            
    except Exception as e:
        print(f"Error starting/stopping OCR process: {e}")
        speak("There was an error trying to run the continuous OCR scanner.")

# --- MEMORY SYSTEM ---
def store_memory(user_statement):
    """
    Uses Gemini to extract key-value pairs from a user's statement and stores them.
    Includes enhanced guidance for simple facts like names.
    """
    
    # Isolate the core statement, stripping multiple trigger and filler words
    statement = user_statement.lower()
    for phrase in ["remember that", "remember", "my name is"]:
        if statement.startswith(phrase):
            statement = statement[len(phrase):].strip()
            break # Stop after finding the first trigger
    
    # Further clean common fillers like "is", "my", "a" from the start of the core fact
    for word in ["my", "is", "a", "that", "the"]:
        if statement.startswith(word + ' '):
            statement = statement[len(word)+1:].strip()
            
    if not statement:
        speak("I heard the word 'remember', but what should I store?")
        return
        
    # ... (rest of system_instruction and Gemini call is fine) ...
    
    system_instruction = (
        "You are an intelligent data extraction system. Your task is to extract "
        "one or more simple, factual key-value pairs from the user's statement. "
        "Each fact MUST be structured with a 'category' and a 'value'. "
        "If the user says 'name is John', the output MUST include "
        "{'category': 'name', 'value': 'John'}. "
        "Reply ONLY with a JSON array containing these objects. If no facts are found, return an empty array ([])."
    )
    
    try:
        # ... (rest of Gemini call and storage logic is fine) ...
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[f"User statement: {statement}"],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "description": "A concise, snake_case category key like 'name' or 'city'"},
                            "value": {"type": "string", "description": "The exact fact or value to store, like 'Demon'"}
                        },
                        "required": ["category", "value"]
                    }
                }
            )
        )
        
        # 1. Parse the JSON array output (Handles markdown code blocks sometimes present in API output)
        try:
            raw_text = response.text.strip().replace("```json", "").replace("```", "")
            extracted_facts_list = json.loads(raw_text)
        except json.JSONDecodeError:
            print(f"Failed to decode JSON from Gemini. Raw response: {response.text}")
            speak("I received unreadable data from the AI. Please try again.")
            return

        # 2. Iterate and Store the facts
        stored_count = 0
        for fact_obj in extracted_facts_list:
            category = fact_obj.get('category')
            value = fact_obj.get('value')
            
            if category and value:
                # Clean up the key before storing
                clean_key = category.lower().replace(" ", "_").replace("'", "")
                user_data['memory'][clean_key] = value
                stored_count += 1
                print(f"💾 Stored fact: {clean_key} = {value}")

        if stored_count > 0:
            # Assumes save_user_data() is correctly defined and accessible.
            save_user_data() 
            speak(f"Okay. I have stored {stored_count} new fact{'s' if stored_count > 1 else ''} for you.")
        else:
            # This is the message you saw in your output
            speak("I couldn't extract any specific, factual information from that to store.")
            
    except Exception as e:
        print(f"Error during memory extraction: {e}")
        speak("I had trouble connecting to the Gemini service. Please check your network.")

# === Main Loop ===
if __name__ == "__main__":
    print("--- Voice Assistant Initialized ---")
    speak("Assistant is online. Say Jarvis.")

    while True:
        # 1. Wait for Hotword
        if hotword_listener(hotword=WAKE_WORD):
            # 2. Cue Response
            speak("Yes, how can I help you?") 
            
            # 3. Listen for Command
            user_input = recognize_speech()
            
            if user_input:
                command = user_input.lower()

                if "exit" in command or "stop" in command:
                    speak("Goodbye!")
                    break

                elif "time" in command:
                    speak(get_current_time())
                    continue

                elif "date" in command:
                    speak(get_current_date())
                    continue

                elif "current weather" in command or "temperature" in command:
                    speak(get_bangalore_weather())
                    continue

                elif "emergency" in command or "send help" in command:
                    send_email("Emergency Alert!", "I need help immediately.", "dheemanthgowda000@gmail.com")
                    continue

                elif "whatsapp" in command:
                    try:
                        speak("To whom should I send the message?")
                        recipient_command = recognize_speech().lower()

                        name = recipient_command.strip()

                        if name in CONTACTS:
                            speak(f"What should I say to {name}?")
                            message = recognize_speech().strip()

                            send_whatsapp_message(name, message)
                            speak(f"Message sent to {name} on WhatsApp.")
                        else:
                            speak(f"I don't have a contact saved for {name}.")

                    except Exception as e:
                        print(f"[ERROR] WhatsApp flow: {e}")
                        speak("Something went wrong while sending the message.")
                    continue

                elif "scan my surroundings" in command or "scan my surrounding" in command or "visual mode" in command:
                    run_scene_description() 
                    continue

                elif "read the text" in command or "start ocr mode" in command:
                    # Run the continuous OCR script for 45 seconds
                    run_ocr_scan() 
                    continue

                elif command.startswith("remember") or command.startswith("my name is"):
                    store_memory(user_input)
                    continue
                
                # Default AI query (calls the direct Gemini API)
                else:
                    reply = ask_jarvis(user_input)
                    speak(reply)