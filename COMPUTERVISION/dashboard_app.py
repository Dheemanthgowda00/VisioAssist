import os
import sys
import time
import subprocess
import signal
from flask import Flask, Response, render_template_string, redirect, url_for, jsonify
from threading import Lock

# --- GLOBAL CONTROL STATE & PORTS ---
MODE_CONFIG = {
    'IDLE': {'port': 5000, 'script': None},
    'OBJECT_DNN': {'port': 5001, 'script': 'object.py'},
    'SCENE_GEMINI': {'port': 5002, 'script': 'scene.py'},
    'OCR_GEMINI': {'port': 5003, 'script': 'text.py'},
}

ACTIVE_MODE = 'IDLE' 
ACTIVE_PROCESS = None
process_lock = Lock() 
# **FIXED:** Using the Pi's actual LAN IP for client redirection
HOST_IP = '192.168.1.94' 
DASHBOARD_PORT = 5000 
CURRENT_STATUS = "System Ready. Select a mode to begin."


# --- HELPER FUNCTIONS FOR PROCESS MANAGEMENT ---

def get_base_path():
    return os.path.dirname(os.path.abspath(__file__))

def stop_active_worker():
    """Sends a SIGINT signal to the worker process to stop it cleanly."""
    global ACTIVE_PROCESS, CURRENT_STATUS, ACTIVE_MODE 
    
    worker_to_stop = ACTIVE_PROCESS
    mode_to_stop = ACTIVE_MODE     

    if worker_to_stop:
        try:
            # 1. Attempt to send SIGINT (Ctrl+C equivalent)
            os.kill(worker_to_stop.pid, signal.SIGINT)
            worker_to_stop.wait(timeout=5)
            CURRENT_STATUS = f"Process {mode_to_stop} (PID {worker_to_stop.pid}) stopped cleanly."
        except subprocess.TimeoutExpired:
            # 3. If it timed out, force kill (SIGKILL)
            worker_to_stop.kill()
            CURRENT_STATUS = f"Process {mode_to_stop} force-killed after timeout."
        except ProcessLookupError:
            CURRENT_STATUS = f"Process {mode_to_stop} was already terminated (PID not found)."
        finally:
            ACTIVE_PROCESS = None
            print(CURRENT_STATUS)

def start_worker(mode):
    """Launches the selected script in a new subprocess."""
    global ACTIVE_PROCESS, CURRENT_STATUS
    
    config = MODE_CONFIG[mode]
    script_path = os.path.join(get_base_path(), config['script'])
    
    try:
        cmd = [sys.executable, script_path]
        
        # Launching with Popen
        worker = subprocess.Popen(cmd, preexec_fn=os.setsid, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Give the process a moment to crash before continuing
        time.sleep(1) 
        if worker.poll() is not None:
             # Process crashed immediately!
             stderr_output = worker.stderr.read().decode('utf-8')
             CURRENT_STATUS = f"Process {mode} LAUNCH FAILED (Exit {worker.poll()}): {stderr_output[:100]}..."
             print(f"WORKER CRASH LOG: {stderr_output}")
             return False

        ACTIVE_PROCESS = worker
        CURRENT_STATUS = f"Launched {mode} on port {config['port']} (PID: {worker.pid})."
        print(f"Worker command: {' '.join(cmd)}")
        print(CURRENT_STATUS)
        return True
    
    except Exception as e:
        CURRENT_STATUS = f"Failed to launch {mode}: {e}"
        print(CURRENT_STATUS)
        return False


# --- FLASK APPLICATION SETUP ---
app = Flask(__name__)

# --- ROUTES ---

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template_string(DASHBOARD_HTML, 
                                  active_mode=ACTIVE_MODE,
                                  status=CURRENT_STATUS,
                                  mode_config=MODE_CONFIG,
                                  dashboard_port=DASHBOARD_PORT)

@app.route('/set_mode/<mode_name>')
def set_mode(mode_name):
    """Stops the current worker and starts the new one."""
    global ACTIVE_MODE, ACTIVE_PROCESS, CURRENT_STATUS
    
    if mode_name not in MODE_CONFIG:
        return f"Invalid mode: {mode_name}", 400

    with process_lock:
        # 1. Stop existing process if running
        stop_active_worker()
        
        # 2. Set the new mode
        ACTIVE_MODE = mode_name
        
        if mode_name != 'IDLE':
            # 3. Start the new worker
            if start_worker(mode_name):
                # SUCCESS PATH: Prepare redirect URL for the JS frontend
                target_port = MODE_CONFIG[mode_name]['port']
                # *** Uses the correct HOST_IP for the client redirect ***
                video_url = f"http://{HOST_IP}:{target_port}/" 
                return jsonify(status='OK', redirect_url=video_url)
            else:
                # LAUNCH FAILED PATH (Status set in start_worker)
                return jsonify(status='ERROR', redirect_url=url_for('index'))
        else:
            # IDLE PATH
            CURRENT_STATUS = "System is IDLE. Select a new task."
            return jsonify(status='IDLE', redirect_url=url_for('index'))

@app.route('/status_feed')
def status_feed():
    """Endpoint for JavaScript to poll the current status and mode."""
    global ACTIVE_MODE, CURRENT_STATUS, ACTIVE_PROCESS 

    # Check if the process unexpectedly died
    if ACTIVE_PROCESS and ACTIVE_PROCESS.poll() is not None:
        exit_code = ACTIVE_PROCESS.poll()
        
        if exit_code != 0:
            CURRENT_STATUS = f"Process {ACTIVE_MODE} FAILED (Exit Code: {exit_code}). Please check logs."
        else:
             CURRENT_STATUS = f"Process {ACTIVE_MODE} exited cleanly."
        
        # Immediately set mode to IDLE and clear the process handle
        ACTIVE_MODE = 'IDLE'
        ACTIVE_PROCESS = None

    # The video stream URL for the active worker
    video_url = None
    if ACTIVE_MODE != 'IDLE':
        port = MODE_CONFIG[ACTIVE_MODE]['port']
        # Note: We return the worker's base URL (Port 500X) here for the JS to display
        video_url = f"http://{HOST_IP}:{port}"

    return jsonify(
        mode=ACTIVE_MODE,
        status=CURRENT_STATUS,
        video_url=video_url
    )


# --- DASHBOARD HTML (Unified Frontend) ---

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Pi Multi-Vision Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; color: #333; margin: 0; }
        .header { background-color: #007bff; color: white; padding: 20px; text-align: center; }
        .controls { display: flex; justify-content: center; padding: 20px; gap: 15px; border-bottom: 2px solid #ccc; }
        .controls button { padding: 10px 20px; font-size: 16px; cursor: pointer; border: none; border-radius: 5px; transition: background-color 0.3s; }
        .controls button:hover { background-color: #0056b3; color: white; }
        .controls button.active { background-color: #28a745; color: white; }
        .content { display: flex; justify-content: center; align-items: flex-start; padding: 30px; }
        .status-box { width: 300px; margin-left: 30px; padding: 20px; background-color: white; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .status-box h2 { color: #007bff; margin-top: 0; }
        #mode-display { font-weight: bold; color: #dc3545; }
        #status-output { white-space: pre-wrap; word-wrap: break-word; font-size: 0.95em; margin-top: 10px; }
        .message { padding: 15px; background-color: #ffe082; border-radius: 5px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Raspberry Pi Multi-Vision Dashboard</h1>
        <p>Active Mode: <span id="mode-display">{{ active_mode }}</span> | Dashboard Port: {{ dashboard_port }}</p>
    </div>
    
    <div class="controls">
        <button onclick="switchMode('IDLE')" id="btn-IDLE" class="{{ 'active' if active_mode == 'IDLE' else '' }}">IDLE / STOP</button>
        <button onclick="switchMode('OBJECT_DNN')" id="btn-OBJECT_DNN" class="{{ 'active' if active_mode == 'OBJECT_DNN' else '' }}">Object Detection (Port 5001)</button>
        <button onclick="switchMode('SCENE_GEMINI')" id="btn-SCENE_GEMINI" class="{{ 'active' if active_mode == 'SCENE_GEMINI' else '' }}">Scene Description (Port 5002)</button>
        <button onclick="switchMode('OCR_GEMINI')" id="btn-OCR_GEMINI" class="{{ 'active' if active_mode == 'OCR_GEMINI' else '' }}">OCR / Text Read (Port 5003)</button>
    </div>
    
    <div class="content">
        <div class="status-box">
            <h2>Instructions</h2>
            <p class="message">Click a mode button to launch the corresponding application on a separate port. The screen will automatically redirect.</p>
        </div>
        <div class="status-box">
            <h2>Current Status</h2>
            <p id="status-output">{{ status }}</p>
        </div>
    </div>

    <script>
        const intervalTime = 1000; // Poll status every 1 second

        function switchMode(newMode) {
            document.querySelectorAll('.controls button').forEach(btn => btn.classList.remove('active'));
            document.getElementById(`btn-${newMode}`).classList.add('active');
            document.getElementById('status-output').innerText = `Attempting to launch ${newMode}...`;
            
            fetch(`/set_mode/${newMode}`)
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'OK') {
                        // **SUCCESS REDIRECTION**
                        // Redirect the browser to the worker's video stream URL (e.g., http://192.168.1.94:5003)
                        window.location.href = data.redirect_url;
                    } else {
                        // Launch failed, update status and keep polling
                        document.getElementById('status-output').innerText = `Launch failed: ${data.status}`;
                        updateStatus();
                    }
                })
                .catch(error => {
                    console.error('Mode switch failed:', error);
                    document.getElementById('status-output').innerText = 'Mode switch failed. Check server log.';
                });
        }
        
        function updateStatus() {
            fetch('/status_feed')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('mode-display').innerText = data.mode;
                    document.getElementById('status-output').innerText = data.status;

                    // Update button highlighting
                    document.querySelectorAll('.controls button').forEach(btn => btn.classList.remove('active'));
                    document.getElementById(`btn-${data.mode}`).classList.add('active');
                })
                .catch(error => {
                    document.getElementById('status-output').innerText = 'Error: Lost connection to dashboard.';
                });
        }

        // Start polling immediately
        setInterval(updateStatus, intervalTime);

        // Initial setup run
        window.onload = updateStatus;
    </script>
</body>
</html>
"""

# --- Script Execution ---

if __name__ == '__main__':
    # Ensure cleanup on application exit
    import atexit
    atexit.register(stop_active_worker) 

    print(f"PiCamera Launcher is running. Access the dashboard at http://{HOST_IP}:{DASHBOARD_PORT}")
    
    try:
        # Start the Flask web server
        app.run(host='0.0.0.0', port=DASHBOARD_PORT, debug=True, use_reloader=False)
    except Exception as e:
        print(f"FATAL ERROR: {e}")