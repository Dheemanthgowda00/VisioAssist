import time
import cv2
import numpy as np
from picamera2 import Picamera2
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
import uvicorn
import asyncio
from concurrent.futures import ThreadPoolExecutor

# --- Configuration ---
# Create a thread pool executor for running blocking camera capture code
# This prevents the synchronous camera operation from blocking FastAPI's main event loop.
executor = ThreadPoolExecutor(max_workers=4)

# --- HTML Template String (Using the same structure) ---
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Raspberry Pi Camera Stream (FastAPI)</title>
    <!-- Tailwind CSS for modern aesthetics -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Apply Inter font */
        body { 
            font-family: 'Inter', sans-serif;
            background-color: #f7f9fb;
            color: #1f2937;
        }
    </style>
</head>
<body class="flex flex-col items-center justify-center min-h-screen p-4">
    <div class="bg-white p-6 md:p-10 rounded-xl shadow-2xl max-w-lg w-full">
        <h1 class="text-3xl font-extrabold text-indigo-600 mb-6 border-b pb-3">
            FastAPI Live Camera Feed
        </h1>
        <p class="text-gray-600 mb-6">
            Motion JPEG stream running asynchronously on the Raspberry Pi.
        </p>
        <img 
            src="/video_feed" 
            width="640" 
            height="480"
            alt="Live Video Stream"
            class="w-full rounded-lg shadow-lg border-4 border-indigo-500"
        >
        <p class="text-sm text-gray-500 mt-4">
            If the stream is delayed or stalls, try reducing the video resolution in the Python code.
        </p>
    </div>
</body>
</html>
"""

# --- Camera Stream Generator Class ---
class CameraStream:
    """
    Handles the synchronous interaction with the Picamera2 module.
    This class's methods will be run in a separate thread to avoid blocking the ASGI server.
    """
    def __init__(self):
        # Initialize Picamera2
        self.picam2 = Picamera2()
        
        # Configure for video (smaller size for faster streaming)
        # Using a slightly lower resolution might prevent memory issues on older Pis
        self.config = self.picam2.create_video_configuration(main={"size": (640, 480)})
        self.picam2.configure(self.config)
        self.picam2.start()
        
        # Allow the camera to warm up
        time.sleep(2)

    def get_frame(self):
        """Captures and encodes a single frame synchronously."""
        # Capture an array from the camera
        frame_array = self.picam2.capture_array()
        
        # Picamera2 often returns BGR, convert to RGB before encoding to ensure proper colors
        frame_array = cv2.cvtColor(frame_array, cv2.COLOR_BGR2RGB)
        
        # OpenCV encodes the array to JPEG bytes for the stream
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90] 
        ret, buffer = cv2.imencode('.jpg', frame_array, encode_param)
        
        return buffer.tobytes()

# --- FastAPI Application Setup ---
app = FastAPI()
camera = CameraStream()

def gen_frames():
    """Synchronous generator function to yield frames."""
    # This synchronous generator will be run by FastAPI in a separate thread pool.
    while True:
        # Blocking call to the camera's synchronous method
        frame = camera.get_frame()
        
        # Yield the frame in the Motion JPEG format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.get('/', response_class=HTMLResponse, summary="Home Page")
async def index():
    """Video streaming home page, renders the embedded HTML string."""
    # Use HTMLResponse to serve the static HTML template
    return HTMLResponse(content=HTML_PAGE, status_code=200)

@app.get('/video_feed', summary="Live Video Stream")
def video_feed():
    """
    Route to serve the streaming video using FastAPI's StreamingResponse.
    Because `gen_frames` is a synchronous generator, FastAPI automatically
    runs it in a separate thread to avoid blocking the main event loop.
    """
    return StreamingResponse(
        gen_frames(),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )

# --- Run the App ---
if __name__ == '__main__':
    # We use uvicorn.run directly, which is the recommended way to start a FastAPI app.
    # The `reload=False` flag is the equivalent of Flask's `use_reloader=False` and
    # is essential when dealing with hardware like picamera2 to prevent it from
    # being initialized twice, leading to "Device or resource busy" errors.
    print("Starting FastAPI camera stream on http://0.0.0.0:5000")
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
