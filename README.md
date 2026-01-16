# VISIOASSIST - Intelligent Vision & Voice Assistant System

A comprehensive Raspberry Pi-based intelligent assistant that combines computer vision, object detection, optical character recognition (OCR), and voice capabilities to provide a multimodal interactive experience.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Architecture](#project-architecture)
- [System Requirements](#system-requirements)
- [Installation & Setup](#installation--setup)
- [Module Documentation](#module-documentation)
- [Usage Guide](#usage-guide)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

VISIOASSIST is an advanced Python-based assistant system designed to run on Raspberry Pi hardware. It leverages multiple AI models and computer vision techniques to provide:

- **Real-time object detection** from camera feed
- **Scene understanding** using Google Gemini AI
- **Text recognition** (OCR) with AI-powered text extraction
- **Voice interaction** with speech recognition and text-to-speech synthesis
- **Smart reminders and notes** management
- **Communication features** (SMS via Twilio, email, etc.)
- **Web-based dashboard** for centralized control

The system is designed to be modular, allowing you to run different modes independently or in sequence based on your needs.

---

## ✨ Features

### Computer Vision & AI Analysis
- **Object Detection**: Real-time detection using SSD MobileNet v3 with COCO dataset
- **Scene Description**: AI-powered scene analysis using Google Gemini 2.5 Flash
- **Text Recognition**: Automated OCR using Gemini's vision capabilities
- **Multi-mode Dashboard**: Web interface to switch between detection modes

### Voice Capabilities
- **Speech-to-Text**: Real-time speech recognition using Vosk
- **Text-to-Speech**: High-quality voice synthesis using Piper
- **Voice Commands**: Natural language processing for command execution
- **Audio Recording**: Direct audio capture from connected earphone/microphone

### Smart Features
- **Reminder System**: Schedule reminders with persistent storage
- **Secure Notes**: Encrypted note storage and retrieval
- **Contact Integration**: WhatsApp and SMS messaging via Twilio
- **Weather Integration**: Real-time weather data fetching
- **Email Support**: Automated email notifications

### Hardware Integration
- **Picamera2**: Camera module control for Raspberry Pi
- **Audio Device Support**: Connected via Bluetooth earphone/microphone
- **Web Streaming**: Real-time camera feed streaming over HTTP

---

## 🏗️ Project Architecture

```
VISIOASSIST/
├── COMPUTERVISION/          # Vision and AI analysis modules
│   ├── dashboard_app.py      # Central web dashboard & mode controller
│   ├── object.py             # Real-time object detection mode
│   ├── scene.py              # Scene description with Gemini AI
│   └── text.py               # OCR text recognition mode
│
├── OBJECTDETECTION/          # Object detection models & utilities
│   ├── detection.py          # Detection model loading & inference
│   ├── detectionv2.py        # Alternative detection implementation
│   ├── coco.names            # COCO dataset class labels
│   ├── ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt  # Model config
│   └── frozen_inference_graph.pb  # Pre-trained weights
│
├── OCR/                       # Optical character recognition
│   └── ocr.py                # Gemini-powered text extraction
│
├── SCENEDESCRIPTION/         # Scene analysis module
│   └── description.py        # Scene understanding using Gemini
│
├── VoiceAssistant/           # Voice interaction & smart features
│   ├── assistant.py          # Main voice assistant with all features
│   ├── assistantv2.py        # Alternative assistant implementation
│   ├── reminder.py           # Reminder scheduling & management
│   ├── secure_notes.py       # Encrypted note storage
│   ├── test_stt.py           # Speech-to-text testing utility
│   ├── test_tts.py           # Text-to-speech testing utility
│   ├── user_data.json        # User profile & settings storage
│   ├── assistant/            # AI models directory
│   │   ├── models/
│   │   │   ├── piper/        # Text-to-speech model (Piper)
│   │   │   └── vosk/         # Speech recognition model (Vosk)
│   │   ├── data/
│   │   │   └── reminders.json    # Scheduled reminders storage
│   │   └── secure/
│   │       └── notes.json        # Encrypted notes storage
│
├── TEST/                      # Testing & experimental modules
│   ├── fastapi_camera.py     # FastAPI camera streaming
│   ├── flask_camera.py       # Flask camera streaming
│   └── image_capture.py      # Image capture utilities
│
├── info.txt                   # System configuration (Python path, device info)
└── README.md                  # This file
```

### Module Dependencies

```
COMPUTERVISION (Dashboard)
    ↓
    ├── OBJECTDETECTION (Object Detection Mode)
    ├── OCR (Text Recognition Mode)
    └── SCENEDESCRIPTION (Scene Analysis Mode)

VoiceAssistant (Independent)
    ├── Uses: Vosk, Piper, OpenRouter API, Twilio
    └── Manages: Reminders, Notes, User Data
```

---

## 🛠️ System Requirements

### Hardware
- **Raspberry Pi 4** (minimum 4GB RAM recommended)
- **Raspberry Pi Camera Module** (Picamera2 compatible)
- **Audio Device**: Bluetooth earphone or USB microphone
- **Network**: WiFi or Ethernet connection
- **Power**: Stable 5V supply

### Software
- **Python 3.10** or higher
- **Linux OS**: Raspberry Pi OS (Bullseye or later)
- **Virtual Environment**: Python venv

### External Dependencies & APIs
- **Google API Key**: For Gemini AI services (scene description, OCR)
- **OpenRouter API Key**: For advanced language models
- **Twilio Account**: For WhatsApp/SMS functionality
- **Weather API Key**: For weather data (optional)

### Python Libraries
- **Computer Vision**: `opencv-python`, `numpy`
- **Camera**: `picamera2`
- **Web Framework**: `flask`
- **AI/ML**: `google-generativeai`, `openai`
- **Voice**: `sounddevice`, `scipy`, `piper-tts`
- **Speech Recognition**: `vosk`, `pyaudio`, `speech_recognition`
- **Communication**: `twilio`, `requests`, `smtplib`
- **Utilities**: `python-dotenv`, `pytz`, `yt_dlp`, `pillow`

---

## 📦 Installation & Setup

### 1. Clone or Download the Project

```bash
cd /home/raspberry
git clone <repository-url> VISIOASSIST
cd VISIOASSIST
```

### 2. Create Python Virtual Environment

```bash
python3.10 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root with the following keys:

```env
# AI & API Keys
GOOGLE_API_KEY=your_google_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
WEATHER_API_KEY=your_weather_api_key_here

# Twilio Configuration (for SMS/WhatsApp)
TWILIO_SID=your_twilio_sid_here
TWILIO_AUTH=your_twilio_auth_token_here

# Email Configuration (optional)
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here

# Hardware & Network
PYTHON_EXECUTABLE=/home/raspberry/VISIOASSIST/venv/bin/python
HOST_IP=192.168.1.94
EARPHONE_MAC=41:42:FF:54:11:F2
```

### 5. Download Pre-trained Models

The object detection models are pre-included in `OBJECTDETECTION/`:
- `frozen_inference_graph.pb` (SSD MobileNet weights)
- `ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt` (Model config)
- `coco.names` (Class labels)

For voice models, they will be automatically downloaded on first use:
- **Vosk**: Speech recognition model
- **Piper**: Text-to-speech model

### 6. Verify Installation

```bash
# Test object detection
python OBJECTDETECTION/detection.py

# Test voice components
python VoiceAssistant/test_stt.py  # Test speech-to-text
python VoiceAssistant/test_tts.py  # Test text-to-speech
```

---

## 📚 Module Documentation

### COMPUTERVISION Module

#### `dashboard_app.py` - Central Control Hub
**Purpose**: Web-based dashboard for managing all vision modes  
**Port**: 5000 (dashboard) + 5001-5003 (worker processes)

**Features**:
- Mode selection interface (Object Detection, Scene Description, OCR)
- Real-time process management with signal handling
- Status monitoring and process lifecycle control
- Multi-port architecture for parallel mode execution

**Usage**:
```bash
python COMPUTERVISION/dashboard_app.py
# Access at http://192.168.1.94:5000
```

#### `object.py` - Real-time Object Detection
**Purpose**: Detect and identify objects in camera feed  
**Model**: SSD MobileNet v3 (COCO-trained)  
**Port**: 5001

**Features**:
- Real-time object bounding boxes
- COCO class labeling (80+ object types)
- Confidence-based filtering
- Live web stream output

**Configuration**:
```python
CONFIDENCE_THRESHOLD = 0.55      # Detection sensitivity
CAMERA_WIDTH, CAMERA_HEIGHT = 640, 480
BOX_COLOR = (255, 0, 0)          # BGR format
```

#### `scene.py` - AI Scene Description
**Purpose**: Generate natural language descriptions of scenes  
**Model**: Google Gemini 2.5 Flash  
**Port**: 5002

**Features**:
- AI-powered scene understanding
- One-sentence natural language descriptions
- Rate-limited API calls (4 RPM for free tier)
- Streaming web interface

**Configuration**:
```python
API_CALL_INTERVAL = 15           # Seconds between Gemini calls
MODEL_NAME = 'gemini-2.5-flash'  # Uses flash for throughput
PROMPT = "Describe what you see in this scene in one sentence."
```

#### `text.py` - OCR Text Recognition
**Purpose**: Extract and recognize text from images  
**Model**: Google Gemini 2.5 Flash (Vision)  
**Port**: 5003

**Features**:
- Automated text extraction from scenes
- Handles printed and handwritten text
- Processes camera feed continuously
- Web-based text display

**Configuration**:
```python
FRAME_INTERVAL = 4               # Seconds between OCR scans
MODEL_NAME = 'gemini-2.5-flash'
GEMINI_OCR_PROMPT = "Analyze the image content. Transcribe ALL text you see..."
```

---

### OBJECTDETECTION Module

#### `detection.py` - Object Detection Engine
**Purpose**: Core object detection implementation  
**Model Used**: SSD MobileNet v3 Large COCO

**Key Functions**:
- `load_model()`: Initialize DNN model with pre-trained weights
- `detect_objects(frame)`: Run inference on a frame
- `draw_boxes()`: Annotate detections on frame
- `video_feed()`: Stream processed video to web client

**Parameters**:
```python
Input Size: 320x320
Scale: 1.0/127.5
Mean: [127.5, 127.5, 127.5]
SwapRB: True
Confidence Threshold: 0.55
```

#### Model Files

| File | Purpose | Size |
|------|---------|------|
| `frozen_inference_graph.pb` | Pre-trained weights | ~178 MB |
| `ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt` | Model architecture config | ~240 KB |
| `coco.names` | 80 COCO object class labels | ~11 KB |

---

### OCR Module

#### `ocr.py` - Optical Character Recognition
**Purpose**: Extract text from images using AI vision

**Key Features**:
- Threading for non-blocking API calls
- Text output caching with lock mechanism
- Configurable scan intervals
- Flask web streaming interface

**Key Functions**:
- `capture_frame()`: Get current camera frame
- `extract_text_with_gemini(image)`: Gemini OCR processing
- `ocr_background_task()`: Continuous text extraction thread
- `video_feed()`: Stream for web display

**Processing Parameters**:
```python
MODEL_NAME = 'gemini-2.5-flash'
FRAME_INTERVAL = 4 seconds
CAMERA_WIDTH, CAMERA_HEIGHT = 640, 480
```

---

### SCENEDESCRIPTION Module

#### `description.py` - Scene Understanding
**Purpose**: Generate intelligent scene descriptions

**Key Features**:
- Real-time scene analysis
- API call rate limiting (15 seconds between calls)
- Thread-safe description updates
- Web streaming interface

**Key Functions**:
- `capture_frame()`: Get camera frame
- `analyze_scene_with_gemini(image)`: Gemini scene analysis
- `description_background_task()`: Continuous analysis thread
- `video_feed()`: Web stream endpoint

**Configuration**:
```python
MODEL_NAME = 'gemini-2.5-flash'
API_CALL_INTERVAL = 15 seconds   # Safe for free tier
PROMPT = "Describe what you see in this scene in one sentence."
```

---

### VoiceAssistant Module

#### `assistant.py` - Comprehensive Voice Assistant
**Purpose**: Main voice interface with AI capabilities

**Features**:
- **Speech Recognition**: Vosk-based STT with continuous listening
- **Text-to-Speech**: Piper ONNX model for natural voice output
- **AI Integration**: OpenRouter API for intelligent responses
- **Contact Management**: Predefined contact list for messaging
- **Reminder System**: Schedule and manage reminders
- **Secure Notes**: Encrypted note storage
- **Communication**: Twilio SMS/WhatsApp, email support
- **Weather Integration**: Real-time weather data
- **YouTube**: Download audio from YouTube videos
- **User Data**: Persistent user profile storage

**Key Functions**:
- `listen_to_audio()`: Continuous speech recognition
- `synthesize_speech(text)`: Text-to-speech conversion
- `send_email(recipient, subject, body)`: Email notifications
- `send_whatsapp_message(contact, message)`: WhatsApp messaging
- `schedule_reminder(message, reminder_time)`: Reminder management
- `save_secure_note(title, content)`: Encrypted note storage
- `get_weather(location)`: Weather information

**Supported Commands**:
- "Send WhatsApp to [contact]"
- "Send email to [recipient]"
- "Set reminder for [time]"
- "Save note [title]"
- "What's the weather"
- "Download audio from [YouTube URL]"
- "Create secure note"

**Configuration**:
```python
CONTACTS = {
    "deepak": "+918867398549"
}

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")

speech_recognition_language = 'en-US'
piper_voice_model = 'en_US-lessac-medium.onnx'
```

#### `reminder.py` - Reminder Management
**Purpose**: Schedule and manage reminders

**Key Functions**:
- `schedule_reminder(message, reminder_time)`: Create new reminder
- `load_existing_reminders()`: Load from persistent storage
- `save_reminders(reminders)`: Persist reminders to JSON
- `check_and_execute_reminders()`: Background reminder checker

**Storage**: `VoiceAssistant/assistant/data/reminders.json`

#### `secure_notes.py` - Encrypted Note Storage
**Purpose**: Secure, encrypted note management

**Key Functions**:
- `save_secure_note(title, content)`: Encrypt and save note
- `load_secure_note(title)`: Retrieve and decrypt note
- `load_notes()`: List all notes

**Storage**: `VoiceAssistant/assistant/secure/notes.json`  
**Encryption**: Built-in Python encryption (fernet-based)

#### `test_stt.py` - Speech-to-Text Testing
**Purpose**: Standalone testing for speech recognition

**Tests**:
- Vosk model loading
- Microphone input capture
- Real-time speech recognition
- Output display

**Usage**:
```bash
python VoiceAssistant/test_stt.py
# Speak into the microphone and see recognized text
```

#### `test_tts.py` - Text-to-Speech Testing
**Purpose**: Standalone testing for voice synthesis

**Tests**:
- Piper model loading
- Text-to-speech conversion
- Audio output playback
- Quality verification

**Usage**:
```bash
python VoiceAssistant/test_tts.py
# Hear synthesized speech output
```

---

### TEST Module

Testing utilities for development and debugging:

#### `fastapi_camera.py`
FastAPI-based camera streaming alternative

#### `flask_camera.py`
Flask-based camera streaming

#### `image_capture.py`
Utility for capturing images from camera and saving to disk

---

## 🚀 Usage Guide

### Starting the Dashboard

```bash
source venv/bin/activate
cd /home/raspberry/VISIOASSIST
python COMPUTERVISION/dashboard_app.py
```

Access the dashboard at: `http://192.168.1.94:5000`

### Running Individual Modes

**Object Detection Mode**:
```bash
python COMPUTERVISION/object.py
# Access at http://192.168.1.94:5001
```

**Scene Description Mode**:
```bash
python COMPUTERVISION/scene.py
# Access at http://192.168.1.94:5002
```

**OCR/Text Recognition Mode**:
```bash
python COMPUTERVISION/text.py
# Access at http://192.168.1.94:5003
```

### Using the Voice Assistant

**Interactive Mode**:
```bash
python VoiceAssistant/assistant.py
# Continuous listening for voice commands
```

**Testing Components**:
```bash
# Test speech recognition
python VoiceAssistant/test_stt.py

# Test text-to-speech
python VoiceAssistant/test_tts.py
```

### Working with Reminders

Reminders are automatically managed through the voice assistant:

```python
from VoiceAssistant.reminder import schedule_reminder, load_existing_reminders

# Schedule a reminder
schedule_reminder("Call mom", "2024-01-16 15:30:00")

# Load existing reminders
reminders = load_existing_reminders()
for reminder in reminders:
    print(f"Reminder: {reminder['message']} at {reminder['time']}")
```

### Managing Secure Notes

Access encrypted notes through the voice assistant:

```python
from VoiceAssistant.secure_notes import save_secure_note, load_secure_note

# Save a note
save_secure_note("passwords", "my_secret_password_123")

# Load a note
content = load_secure_note("passwords")
print(content)
```

---

## ⚙️ Configuration

### Key Configuration Files

#### `info.txt`
Contains system-level configuration:
```
python - /home/raspberry/VISIOASSIST/venv310/bin/python
earphone - 41:42:FF:54:11:F2
```

#### `.env` File (Required)
Create at project root with API keys and credentials:

```env
# Google Gemini API
GOOGLE_API_KEY=AIzaSy...

# OpenRouter LLM API
OPENROUTER_API_KEY=sk-or-v1...

# Twilio SMS/WhatsApp
TWILIO_SID=AC...
TWILIO_AUTH=your_token...

# Weather (OpenWeatherMap or similar)
WEATHER_API_KEY=your_key...

# Email (Gmail SMTP)
EMAIL_ADDRESS=your@gmail.com
EMAIL_PASSWORD=your_app_password...
```

### Object Detection Configuration

In `OBJECTDETECTION/detection.py`:
```python
CONFIDENCE_THRESHOLD = 0.55          # Adjust detection sensitivity
CAMERA_WIDTH, CAMERA_HEIGHT = 640, 480
FONT_SCALE = 2
FONT_THICKNESS = 2
```

### Voice Assistant Configuration

In `VoiceAssistant/assistant.py`:
```python
CONTACTS = {
    "deepak": "+918867398549"
}
speech_recognition_language = 'en-US'
```

### Gemini API Configuration

In scene and OCR modules:
```python
MODEL_NAME = 'gemini-2.5-flash'      # Fast model for free tier
API_CALL_INTERVAL = 15               # Rate limiting (seconds)
```

---

## 🐛 Troubleshooting

### Common Issues & Solutions

#### 1. **Picamera2 Not Initializing**

**Problem**: `Error initializing Picamera2`

**Solutions**:
```bash
# Ensure camera is enabled in raspi-config
sudo raspi-config
# Navigate to: Interface Options > Camera > Enable

# Update camera packages
sudo apt update
sudo apt install -y python3-picamera2

# Check camera availability
libcamera-hello --list-cameras
```

#### 2. **Vosk Speech Recognition Not Working**

**Problem**: `ModuleNotFoundError: No module named 'vosk'` or no audio input

**Solutions**:
```bash
# Install vosk and dependencies
pip install vosk pyaudio pocketsphinx

# Check microphone
python -m sounddevice --list-devices

# Verify audio permissions
groups | grep audio
sudo usermod -a -G audio $USER
```

#### 3. **Gemini API Rate Limiting**

**Problem**: `RESOURCE_EXHAUSTED` error from Gemini API

**Solutions**:
- Increase `API_CALL_INTERVAL` in scene.py and ocr.py
- Use `gemini-2.5-flash` instead of `-pro` model
- Check your API quota at Google AI Studio
- Consider upgrading to paid tier if free tier is insufficient

#### 4. **Flask Port Already in Use**

**Problem**: `Address already in use` error

**Solutions**:
```bash
# Find process using port
sudo lsof -i :5000
sudo lsof -i :5001
sudo lsof -i :5002
sudo lsof -i :5003

# Kill the process
sudo kill -9 <PID>

# Or change HOST_IP in dashboard_app.py
```

#### 5. **Piper TTS Model Not Found**

**Problem**: `FileNotFoundError: piper model file`

**Solutions**:
```bash
# Models download on first run, but you can pre-download:
mkdir -p VoiceAssistant/assistant/models/piper
cd VoiceAssistant/assistant/models/piper

# Download manually if needed
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
```

#### 6. **Email/SMTP Not Working**

**Problem**: `SMTPAuthenticationError` or email not sending

**Solutions**:
```
# For Gmail: Use 16-character App Password (not regular password)
# Enable "Less secure app access" or use App Passwords
# https://myaccount.google.com/apppasswords

# Verify credentials in .env file
EMAIL_ADDRESS=your@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx  # 16-char app password
```

#### 7. **Twilio WhatsApp Not Sending**

**Problem**: `Unable to create record: The number is not a valid phone number`

**Solutions**:
```python
# Ensure phone numbers include country code
CONTACTS = {
    "deepak": "+918867398549"  # Include +91 for India
}

# Verify Twilio account is set up for WhatsApp
# Use Twilio sandbox numbers for testing
```

#### 8. **Web Dashboard Not Accessible**

**Problem**: `Connection refused` when accessing http://192.168.1.94:5000

**Solutions**:
```bash
# Check if dashboard is running
ps aux | grep dashboard_app.py

# Verify IP address (might differ from 192.168.1.94)
hostname -I

# Check firewall rules
sudo ufw status

# Ensure process is binding to 0.0.0.0
# In dashboard_app.py: app.run(host='0.0.0.0', port=5000)
```

#### 9. **Out of Memory Errors**

**Problem**: `MemoryError` or system freezing

**Solutions**:
- Close unnecessary services: `sudo service lightdm stop`
- Reduce camera resolution in configuration
- Limit concurrent modes (run one at a time)
- Monitor memory: `free -h`, `top`

#### 10. **Model File Corruption**

**Problem**: Weights file is corrupted or incomplete

**Solutions**:
```bash
# Verify file integrity
md5sum OBJECTDETECTION/frozen_inference_graph.pb

# Re-download if needed:
# Check the official TensorFlow detection model zoo
```

---

## 📊 Performance & Optimization

### Memory Optimization
- Each mode (object detection, OCR, scene description) runs independently
- Models are loaded once and cached in memory
- Threading used for non-blocking API calls

### API Rate Limiting
- **Gemini**: 15-second interval for free tier (4 RPM)
- **OpenRouter**: Configurable based on tier
- **Weather API**: Query only on demand or scheduled intervals

### Camera Configuration
- Default resolution: 640x480 (balance of speed and quality)
- FPS: Depends on model inference time (~1-2 FPS for object detection)
- Format: BGR888 for OpenCV compatibility

---

## 📝 Project Structure Notes

### Configuration Hierarchy
1. Hardcoded defaults in module files
2. Environment variables from `.env`
3. Runtime configuration through CLI arguments

### Data Storage
```
VoiceAssistant/
├── user_data.json              # User profiles
├── assistant/data/reminders.json   # Scheduled reminders
└── assistant/secure/notes.json     # Encrypted notes
```

### Model Storage
```
VoiceAssistant/assistant/models/
├── piper/                      # TTS models (auto-downloaded)
└── vosk/                        # STT models (auto-downloaded)
```

---

## 🔒 Security Considerations

1. **API Keys**: Never commit `.env` to git; use `.gitignore`
2. **Secure Notes**: Encrypted with Fernet (symmetric encryption)
3. **User Data**: JSON storage (plaintext) - implement encryption for sensitive data
4. **Network Access**: Dashboard accessible on local network only (verify firewall)
5. **Twilio Credentials**: Store in environment variables, not in code

---

## 🤝 Contributing & Development

### Adding New Modes
1. Create new module in `COMPUTERVISION/`
2. Implement Flask app with video_feed() endpoint
3. Register in `MODE_CONFIG` in dashboard_app.py
4. Update port assignments

### Testing New Features
```bash
# Use TEST/ module files as templates
python TEST/image_capture.py    # Test image capture
python VoiceAssistant/test_stt.py  # Test STT
python VoiceAssistant/test_tts.py  # Test TTS
```

---

## 📞 Support & Resources

### External Documentation
- **Gemini API**: https://ai.google.dev/docs
- **OpenRouter**: https://openrouter.ai/docs
- **Twilio**: https://www.twilio.com/docs
- **Vosk**: https://alphacephei.com/vosk/
- **Piper TTS**: https://github.com/rhasspy/piper

### Debugging Commands
```bash
# Check GPU/Memory
cat /proc/cpuinfo
free -h

# View logs
dmesg | tail -20

# Monitor processes
top -u $(whoami)

# Test connectivity
ping 8.8.8.8
curl -I https://api.openai.com
```

---

## 📄 License

This project is intended for personal use on Raspberry Pi systems. Refer to individual model licenses:
- SSD MobileNet: TensorFlow Model Zoo
- Vosk: Apache 2.0
- Piper TTS: MIT

---

## ✅ Quick Start Checklist

- [ ] Raspberry Pi with camera module enabled
- [ ] Python 3.10+ and virtual environment setup
- [ ] All dependencies installed via pip
- [ ] `.env` file created with API keys
- [ ] Picamera2 and audio devices configured
- [ ] Test individual components (STT, TTS, detection)
- [ ] Dashboard accessible on network
- [ ] Voice assistant responding to commands

---

**Last Updated**: January 16, 2026  
**Status**: Active Development
