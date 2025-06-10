import speech_recognition as sr
import pyttsx3
import datetime
import requests
import smtplib
from email.mime.text import MIMEText
import os
import time
import vlc
import yt_dlp
from twilio.rest import Client
from dotenv import load_dotenv
import subprocess

player = None
paused = False
stop_flag = False

load_dotenv()

account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
from_whatsapp_number = 'whatsapp:+14155238886'

contacts = {
    "deepak aditya": "+918867398549",
    "jane": "+919876543210"
}

def speak(text):
    print(f"Assistant: {text}")
    try:
        subprocess.run(['espeak', text], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    except Exception as e:
        print(f"Error in speech synthesis: {e}")

def tell_time():
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    speak(f"The current time is {current_time}")

def tell_date():
    current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
    speak(f"Today is {current_date}")

def get_weather(city):
    try:
        api_key = "41a3a5814959d1dc9b18a8148a587813";
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url).json()
        if response["cod"] != 200:
            speak(f"City {city} not found.")
            return
        weather = response["weather"][0]["description"]
        temp = response["main"]["temp"]
        speak(f"The weather in {city} is {weather} with a temperature of {temp} degrees Celsius.")
    except Exception as e:
        speak("Sorry, I couldn't fetch the weather right now.")

def send_sos_alert():
    sos_message = "Emergency! Please check on me immediately. This is an automated message from my assistant."

    # Email settings
    sender_email = "bdheemanth00@gmail.com"
    receiver_email = "dheemanthgowda000@gmail.com"
    password = "tnrqocjayqusrfvn" # Store password securely in environment variables
    subject = "SOS Alert"

    # Create email content
    msg = MIMEText(sos_message)
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    try:
        # Set up the server
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.close()
        speak("SOS alert has been sent successfully.")
    except Exception as e:
        speak(f"Sorry, I couldn't send the SOS alert. Error: {e}")

def listen():
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source)
            speak("I'm listening...")
            audio = r.listen(source)
            command = r.recognize_google(audio).lower()
            print(f"You said: {command}")
            return command
    except sr.UnknownValueError:
        speak("Sorry, I didn't catch that.")
        return ""
    except sr.RequestError:
        speak("Network error while recognizing.")
        return ""

def run_ocr_for_10_seconds():
    speak("Starting OCR. Please hold the camera steady.")
    ocr_process = subprocess.Popen(["python3", "/home/raspberry/VisioAssist_Final/OCR_core/OCR_core.py"])
    time.sleep(10)  # Run OCR for 10 seconds
    ocr_process.terminate()
    speak("OCR has been stopped.")

def run_detection_for_25_seconds():
    speak("Starting Object Detection. Please hold the camera steady.")
    ocr_process = subprocess.Popen(["python3", "/home/raspberry/VisioAssist_Final/object_detection/Detection.py"])
    time.sleep(25)  # Run OCR for 10 seconds
    ocr_process.terminate()
    speak("Object Detection has been stopped.")

def run_fire_for_40_seconds():
    speak("Starting Fire Detection")
    ocr_process = subprocess.Popen(["python3", "/home/raspberry/VisioAssist_Final/FireDetection_core/fire_detection_core.py"])
    time.sleep(40)  # Run OCR for 10 seconds
    ocr_process.terminate()
    speak("fire Detection has been stopped.")

def calculate(expression):
    try:
        result = eval(expression)
        speak(f"The answer is {result}")
    except:
        speak("Sorry, I couldn't calculate that.")

def record_voice_note():
    speak("Please start speaking your note. Say 'stop' when you're done.")

    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        speak("I'm listening...")

        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=30)
            text = recognizer.recognize_google(audio)

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"voice_note_{timestamp}.txt"
            with open(filename, 'w') as file:
                file.write(text)

            speak(f"Your note has been saved at {timestamp.replace('_', ' ').replace('-', ':')}")

        except sr.UnknownValueError:
            speak("Sorry, I couldn't understand the audio.")
        except sr.RequestError as e:
            speak(f"Could not request results; {e}")

def play_all_notes():
    notes = [f for f in os.listdir('.') if f.startswith("voice_note_") and f.endswith(".txt")]
    notes.sort()  # Ensures chronological order

    if not notes:
        speak("No voice notes found.")
        return

    speak(f"You have {len(notes)} notes. I will read them one by one.")

    for i, note in enumerate(notes):
        timestamp = note.replace("voice_note_", "").replace(".txt", "").replace("_", " ").replace("-", ":")
        with open(note, 'r') as file:
            content = file.read()
            speak(f"Note {i + 1}, recorded at {timestamp}: {content}")
            time.sleep(1)  # Pause between notes

def delete_voice_note():
    notes = [f for f in os.listdir('.') if f.startswith("voice_note_") and f.endswith(".txt")]
    notes.sort()

    if not notes:
        speak("No voice notes to delete.")
        return

    speak("Here are your notes. Say 'delete note' followed by the number of the note you want to delete.")

    for i, note in enumerate(notes):
        timestamp = note.replace("voice_note_", "").replace(".txt", "").replace("_", " ").replace("-", ":")
        with open(note, 'r') as file:
            content = file.read()
            speak(f"Note {i + 1}, recorded at {timestamp} : {content}")
            time.sleep(1)  # Pause between notes

    # Listen for command to delete a specific note (e.g., "delete note 3")
    command = listen()

    if "delete note" in command:
        try:
            # Extract the number from the command
            parts = command.split()
            note_number = int(parts[-1])  # Get the last word as the note number

            # Check if the number is valid
            if 1 <= note_number <= len(notes):
                os.remove(notes[note_number - 1])
                speak(f"Note {note_number} has been deleted.")
            else:
                speak("Invalid note number.")
        except (ValueError, IndexError):
            speak("I couldn't understand the note number.")
    else:
        speak("I didn't hear a valid command to delete a note.")

def send_whatsapp_message(body, to):
    """Function to send a message to a specified WhatsApp number using Twilio"""
    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=body,
            from_=from_whatsapp_number,
            to=f'whatsapp:{to}'
        )
        print(f"Message SID: {message.sid}")
        speak("Your message has been sent.")
    except Exception as e:
        print(f"Error sending message: {e}")
        speak("Failed to send message. Check if the number joined the sandbox.")

def listen_for_message():
    """Function to listen to the user's voice input for the message content"""
    speak("Please say the message you want to send.")
    return listen()

def listen_for_recipient():
    """Function to listen to the user's voice input for the recipient's name"""
    speak("Please say the recipient's name.")
    return listen()

def send_message_via_whatsapp():
    """Main function to send a WhatsApp message via Twilio"""
    # Step 1: Listen for message content
    message = listen_for_message()

    if message:  # If the message was captured
        # Step 2: Listen for recipient's name
        name = listen_for_recipient()

        # Step 3: Check if the recipient exists in the contacts list
        if name and name.lower() in contacts:
            recipient_number = contacts[name.lower()]
            send_whatsapp_message(message, recipient_number)
        else:
            speak("Sorry, I couldn't find that contact.")
    else:
        speak("No message received.")

def main():
    speak("Hello! I am your voice assistant. How can I help you?")
    while True:
        command = listen()
        if "time" in command:
            tell_time()
        elif "date" in command:
            tell_date()
        elif "climate" in command:
            speak("Please tell me the city name.")
            city = listen()
            get_weather(city)
        elif "sos" in command:
            send_sos_alert()
        elif "read" in command:
            run_ocr_for_10_seconds()
        elif "object" in command:
            run_detection_for_25_seconds()
        elif "fire" in command:
            run_fire_for_40_seconds()
        elif "calculate" in command:
            speak("Please say the expression.")
            expr = listen().replace('x', '*').replace('into', '*').replace('plus', '+').replace('minus', '-').replace('divided by', '/')
            calculate(expr)
        elif "record note" in command:
            record_voice_note()
        elif "play note" in command:
            play_all_notes()
        elif "delete note" in command:
            delete_voice_note()
        elif "send message" in command or "whatsapp" in command:
            send_message_via_whatsapp()
        elif "exit" in command or "goodbye" in command:
            speak("Goodbye! Have a nice day.")
            break
        elif command == "":
            continue
        else:
            speak("Sorry, I didn't understand that. Try asking for the time, date, or weather.")

if __name__ == "__main__":
    main()
