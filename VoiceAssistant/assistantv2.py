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
# ----------------------------
from dotenv import load_dotenv
import datetime
import pytz
from twilio.rest import Client
import smtplib
from email.mime.text import MIMEText


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

# Load User Data
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}
user_data = load_user_data()

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
def ask_jarvis(prompt):
    """
    Sends prompt to Gemini 2.5 Flash with live date context and system instructions.
    """
    
    # 1. Inject Live Date Context 
    india = pytz.timezone("Asia/Kolkata")
    current_time_date = datetime.datetime.now(india).strftime("%A, %d %B %Y, %I:%M %p %Z")
    
    # 2. Construct System Instruction
    system_instruction = (
        f"You are Navis, a helpful and highly intelligent assistant. "
        f"The current date and time is {current_time_date}. "
        f"Use your internal knowledge and real-time grounding capabilities to answer current events questions accurately. "
        f"Reply concisely, in less than 30 words."
    )

    # 3. Call the Gemini API
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            )
        )
        return response.text.strip()
    except Exception as e:
        print(f"Error during Gemini API call: {e}")
        return "I had trouble connecting to the Gemini service. Please check your network and API key."


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
                
                # Default AI query (calls the direct Gemini API)
                else:
                    reply = ask_jarvis(user_input)
                    speak(reply)