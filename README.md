# VisioAssist

# VisioAssist 🎙️👁️  
**A Raspberry Pi-based Voice Assistant for the Visually Impaired**

VisioAssist is a modular, AI-powered assistant tailored for the blind and visually impaired. Built on Python 3.7 and optimized for the Raspberry Pi 4, it offers voice-guided assistance with real-time object recognition, fire detection, OCR, voice notes, WhatsApp messaging, SOS alerts, and more — all using a USB webcam with mic and standard 3.5mm jack headphones.

---

## 🔧 Hardware Requirements

- 🧠 **Raspberry Pi 4 (64-bit)**
- 📷 **USB Webcam with built-in Microphone**
- 🎧 **3.5mm Jack Headphones**
- 💾 MicroSD card (32GB+ recommended)
- 🔌 Internet access (Wi-Fi or Ethernet)

---

## 🧰 Software Stack

- **Python 3.7**
- **OpenCV**
- **Ultralytics YOLOv8** (Fire detection)
- **TensorFlow (Object Detection API)**
- **SpeechRecognition**
- **eSpeak** (Text-to-speech)
- **VLC & yt_dlp** (YouTube music playback)
- **Twilio API** (WhatsApp Messaging)
- **OCR.space API** (Text recognition)

---

## 💡 Features

| Feature                | Description |
|------------------------|-------------|
| 🎤 **Voice Control**   | Use voice commands to trigger assistant actions |
| 🕐 **Time & Date**     | Ask for the current time and date |
| 🌤 **Weather Updates** | Get real-time weather reports (via OpenWeatherMap) |
| 🧯 **Fire Detection**  | Real-time fire detection using custom-trained YOLOv8 |
| 📦 **Object Detection**| Real-time object detection using MobileNet SSD |
| 📖 **OCR Reading**     | Reads printed text using camera and OCR.space API |
| 📝 **Voice Notes**     | Record, play, and delete voice notes locally |
| 🆘 **SOS Alerts**      | Sends an email alert in case of emergency |
| 📲 **WhatsApp Support**| Send messages via Twilio WhatsApp API |
| 🧮 **Calculator**      | Speak and evaluate arithmetic expressions |

---

## 🗣️ Voice Commands Supported

- `"time"` – Tells the current time
- `"date"` – Reads today’s date
- `"climate"` – Prompts for city and reads weather
- `"sos"` – Sends SOS email
- `"read"` – Triggers OCR for 10 seconds
- `"object"` – Runs object detection for 25 seconds
- `"fire"` – Runs fire detection for 40 seconds
- `"record note"` – Saves a spoken voice note
- `"play note"` – Plays all saved notes
- `"delete note"` – Deletes selected voice notes
- `"send message"` or `"whatsapp"` – Sends WhatsApp message via Twilio
- `"calculate"` – Calculates spoken math expressions
- `"exit"` or `"goodbye"` – Exits the assistant

---

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/VisioAssist.git
cd VisioAssist_Final

