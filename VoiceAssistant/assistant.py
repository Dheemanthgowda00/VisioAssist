import os
import sys
import time
import json
import subprocess
import requests
import sounddevice as sd
import numpy as np
import scipy.signal
from piper.voice import PiperVoice
import speech_recognition as sr
from dotenv import load_dotenv
import signal
import datetime
import pytz
import smtplib
from email.mime.text import MIMEText
import yt_dlp
import subprocess
from secure_notes import save_secure_note, load_secure_note, load_notes
from reminder import schedule_reminder, load_existing_reminders
from twilio.rest import Client
from dotenv import load_dotenv
import os

load_dotenv()

# Twilio credentials
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_WHATSAPP = "whatsapp:+14155238886"  # Twilio sandbox number

client = Client(TWILIO_SID, TWILIO_AUTH)

# Contact mapping (name to number)
CONTACTS = {
    "deepak": "+918867398549"
}

# Load OpenRouter API key from .env
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
weather_api_key = os.getenv("WEATHER_API_KEY")

# === User Data Handling ===
USER_DATA_FILE = "user_data.json"

def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

user_data = load_user_data()

# === Speak Function ===
# Initialize Piper voice model once
voice = PiperVoice.load("assistant/models/piper/en_US-lessac-medium.onnx")  # Adjust path if needed

def speak(text):
    print(f"Navis: {text}")
    audio_chunks = voice.synthesize(text)

    # Concatenate audio data
    audio_bytes = b"".join(chunk.audio_int16_bytes for chunk in audio_chunks)
    audio_array = np.frombuffer(audio_bytes, dtype=np.int16)

    # Optional: Adjust volume and speed
    audio_array = (audio_array * 1.0).astype(np.int16)  # Volume scaling (1.0 = 100%)
    original_rate = 16000
    slowed_rate = int(original_rate * 1.0)  # Speed adjustment (1.0 = normal)

    number_of_samples = int(len(audio_array) * original_rate / slowed_rate)
    slowed_audio = scipy.signal.resample(audio_array, number_of_samples).astype(np.int16)

    # Play audio
    sd.play(slowed_audio, samplerate=original_rate)
    sd.wait()

load_existing_reminders(speak)


# === Listen Function ===
def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Speak now...")
        r.adjust_for_ambient_noise(source)

        try:
            # Increase listen time here
            audio = r.listen(source, timeout=10, phrase_time_limit=7)
            text = r.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Could not understand audio.")
            speak("Sorry, I didn't catch that.")
            return None
        except sr.RequestError:
            print("Could not request results from Google Speech Recognition.")
            speak("Speech recognition service is unavailable.")
            return None
        
def hotword_listener(hotword="alexa"):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for hotword...")
        r.adjust_for_ambient_noise(source)
        try:
            audio = r.listen(source, timeout=10, phrase_time_limit=3)
            trigger = r.recognize_google(audio).lower()
            print(f"Heard: {trigger}")
            return hotword in trigger
        except:
            return False
        
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
        msg = client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP,
            to=to_number
        )
        speak(f"Message sent to {contact_name} on WhatsApp.")
    except Exception as e:
        print(f"Twilio Error: {e}")
        speak("Failed to send the WhatsApp message.")


# === Object Detection Handler ===
def run_object_detection():
    speak("Starting object detection for 25 seconds.")
    process = subprocess.Popen([sys.executable, "/home/raspberry/VISIOASSIST/ObjectDetection/detection.py"])
    time.sleep(25)
    process.terminate()
    try:
        process.wait(timeout=2)
        speak("Object detection completed.")
    except subprocess.TimeoutExpired:
        process.kill()
        speak("Object detection was forcibly stopped.")

# === OCR Handler ===
def run_ocr_reader():
    speak("Starting text recognition.")
    process = subprocess.Popen([sys.executable, "/home/raspberry/VISIOASSIST/OCR/ocr.py"])
    process.wait()  # Wait until OCR script finishes on its own
    speak("Text recognition completed.")


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


# === Store memory facts from speech ===
def extract_and_store_fact(user_input, user_data):
    system_prompt = (
        "You're a personal assistant that stores facts the user tells you. "
        "If the user is telling you a personal fact (like 'I work at Robomanthan', 'my dog's name is Rocky', or 'my favorite food is pizza'), "
        "extract and return it as a JSON object like {\"key\": \"workplace\", \"value\": \"Robomanthan\"}. "
        "You may choose keys like 'workplace', 'birthday', 'name', 'hobby', 'favorite_food', etc. "
        "If the input is not a fact, return null."
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://yourapp.com",
        "X-Title": "Alexa-assistant"
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        if response.status_code == 200:
            reply = response.json()['choices'][0]['message']['content']
            try:
                fact = json.loads(reply)
                if isinstance(fact, dict) and "key" in fact and "value" in fact:
                    user_data[fact["key"]] = fact["value"]
                    save_user_data(user_data)
                    speak(f"Got it. I'll remember your {fact['key']} is {fact['value']}.")
                    return True
            except json.JSONDecodeError:
                pass
    except Exception as e:
        print(f"Error during fact extraction: {e}")
        speak("There was an issue connecting to the server.")

    return False

# === Ask AI Assistant (OpenRouter) ===
def ask_jarvis(prompt):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://yourapp.com",
        "X-Title": "Navis-assistant"
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": f"You are Alexa, a helpful and intelligent assistant. The user's name is {user_data.get('name', 'unknown')}. Reply in less than 30 words."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        if response.status_code == 200:
            reply = response.json()['choices'][0]['message']['content']
            return reply.strip()
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        print(f"Error during OpenRouter API call: {e}")
        return "There was a problem reaching the assistant."

# === Main Loop ===
if __name__ == "__main__":
    print("Alexa with Voice is online. Say 'exit' to quit.\n")
    speak("Alexa is online. Say something.")

    while True:
        if hotword_listener():  # wait for "Navis"
            speak("Yes, how can I help you?")
            user_input = listen()
            if user_input:
                command = user_input.lower()

                if command in ["exit", "quit", "stop"]:
                    speak("Goodbye!")
                    break

                elif "current time" in command:
                    speak(get_current_time())
                    continue

                elif "current date" in command:
                    speak(get_current_date())
                    continue

                elif "current weather" in command or "temperature" in command:
                    speak(get_bangalore_weather())
                    continue

                elif "object detection" in command or "detect objects" in command:
                    run_object_detection()
                    continue

                elif "read text" in command or "text recognition" in command or "perform ocr" in command:
                    run_ocr_reader()
                    continue

                elif "emergency" in command or "send help" in command:
                    send_email("Emergency Alert!", "I need help immediately.", "dheemanthgowda000@gmail.com")
                    continue

                elif "whatsapp" in command:
                    try:
                        speak("To whom should I send the message?")
                        recipient_command = listen().lower()

                        name = recipient_command.strip()

                        if name in CONTACTS:
                            speak(f"What should I say to {name}?")
                            message = listen().strip()

                            send_whatsapp_message(name, message)
                            speak(f"Message sent to {name} on WhatsApp.")
                        else:
                            speak(f"I don't have a contact saved for {name}.")

                    except Exception as e:
                        print(f"[ERROR] WhatsApp flow: {e}")
                        speak("Something went wrong while sending the message.")
                    continue


                elif "remind me" in command:
                    try:
                        reminder_phrase = command.split("remind me")[1].strip()
                        schedule_reminder(reminder_phrase, speak)
                    except:
                        speak("Sorry, I couldn't set the reminder.")
                    continue

                elif "remember" in command and "is" in command:
                    try:
                        
                        parts = command.replace("remember", "").strip().split(" is ")
                        title = parts[0].replace("my", "").strip()
                        content = parts[1].strip()
                        save_secure_note(title, content)
                        speak(f"I've securely stored your {title}.")
                    except:
                        speak("Sorry, I couldn't store that securely.")
                    continue

                elif "recall" in command :
                    speak("Please say your voice password to continue.")
                    password_attempt = listen()
                    if password_attempt and "bingo" in password_attempt.lower():
                        for key in load_notes():
                            if key in command:
                                note = load_secure_note(key)
                                if note:
                                    speak(f"Your {key} is {note}.")
                                else:
                                    speak("Sorry, I couldn't retrieve that.")
                                break
                        else:
                            speak("I couldn't find that note.")
                    else:
                        speak("Wrong password. Access denied.")
                    continue

                elif any(x in command for x in ["what is my", "when is my", "tell me my"]):
                    matched = False
                    for key in user_data:
                        if key.lower() in command:
                            speak(f"Your {key} is {user_data[key]}.")
                            matched = True
                            break
                    if not matched:
                        speak("I couldn't find that information in my memory.")
                    continue

                # if extract_and_store_fact(user_input, user_data):
                #     continue

                reply = ask_jarvis(user_input)
                print(f"Alexa: {reply}\n")
                speak(reply)
