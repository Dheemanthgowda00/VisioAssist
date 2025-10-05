from picamera2 import Picamera2
import time

# Initialize the camera object
picam2 = Picamera2()

# Configure the camera for a still capture
# This configuration uses the maximum resolution for still images
camera_config = picam2.create_still_configuration(main={"size": (4608, 2592)})
picam2.configure(camera_config)

print("Starting camera...")
picam2.start()

# Give the camera a brief moment to set exposure and focus
time.sleep(2)

# Capture the image
filename = "test_image.jpg"
print(f"Capturing image and saving as {filename}...")
picam2.capture_file(filename)

# Stop the camera
picam2.stop()
print("Capture complete. Camera stopped.")