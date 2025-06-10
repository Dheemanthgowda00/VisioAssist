import cv2
import requests
import time
import subprocess

# OCR.space API key and endpoint
api_key = 'ab8bd882d488957'
url = 'https://api.ocr.space/parse/image'

# Initialize camera (try 0 or 1 depending on your setup)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

print("📷 Starting headless real-time OCR with voice. Press Ctrl+C to stop.")

frame_count = 0
process_interval = 5  # Process every 5 frames
last_spoken_text = ""

def speak_text(text):
    # Use espeak piped to aplay (this works with your setup)
    subprocess.run(f'espeak \"{text}\" --stdout | aplay', shell=True)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame.")
            time.sleep(0.5)
            continue

        if frame_count % process_interval == 0:
            image_path = "temp_frame.jpg"
            cv2.imwrite(image_path, frame)

            with open(image_path, 'rb') as image_file:
                response = requests.post(
                    url,
                    files={'image': image_file},
                    data={'apikey': api_key}
                )

            try:
                result = response.json()
                if result.get('IsErroredOnProcessing') is False:
                    extracted_text = result['ParsedResults'][0]['ParsedText'].strip()
                    if extracted_text and extracted_text != last_spoken_text:
                        print("📝 Extracted Text:", extracted_text)
                        speak_text(extracted_text)
                        last_spoken_text = extracted_text
                else:
                    print("OCR Error:", result.get('ErrorMessage'))
            except Exception as e:
                print("❌ Failed to parse OCR response:", e)

            time.sleep(0.5)

        frame_count += 1

except KeyboardInterrupt:
    print("\n🛑 Stopping OCR...")

finally:
    cap.release()
