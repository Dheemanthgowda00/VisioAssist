from flask import Flask, render_template, Response, request, redirect, url_for
import cv2
import os
import face_recognition
from simple_facerec import SimpleFacerec

app = Flask(__name__)

UPLOAD_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

sfr = SimpleFacerec()
sfr.load_encoding_images("images/")

# Dynamic faces
dynamic_encodings = []
dynamic_names = []

# Webcam and detection control
camera = None
detection_active = False

def generate_frames():
    global camera, detection_active
    if camera is None:
        camera = cv2.VideoCapture(0)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    while detection_active:
        success, frame = camera.read()
        if not success:
            break

        frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=20)

        # Known faces from images/ folder
        face_locations, face_names = sfr.detect_known_faces(frame)

        # Dynamic face match
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb_small_frame)
        encodings = face_recognition.face_encodings(rgb_small_frame, locations)

        for (top, right, bottom, left), face_encoding in zip(locations, encodings):
            matches = face_recognition.compare_faces(dynamic_encodings, face_encoding)
            name = "Unknown"
            color = (0, 0, 255)  # Red for unknown

            if True in matches:
                match_index = matches.index(True)
                name = dynamic_names[match_index]
                color = (0, 255, 0)  # Green for known

            # Scale back up
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    # global detection_active
    # detection_active = False
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    global dynamic_encodings, dynamic_names, detection_active
    if 'image' not in request.files or 'name' not in request.form:
        return "Missing data", 400

    file = request.files['image']
    user_name = request.form['name'].strip()

    if file.filename == '' or user_name == '':
        return "No file or name provided", 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'uploaded.jpg')
    file.save(filepath)

    image = face_recognition.load_image_file(filepath)
    encodings = face_recognition.face_encodings(image)

    if len(encodings) == 0:
        return "No face detected in uploaded image.", 400

    dynamic_encodings = [encodings[0]]
    dynamic_names = [user_name]
    detection_active = True
    return redirect(url_for('live'))

@app.route('/live')
def live():
    return render_template('live.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stop')
def stop():
    global detection_active, camera
    detection_active = False
    if camera is not None:
        camera.release()
        camera = None
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
