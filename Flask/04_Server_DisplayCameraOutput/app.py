from flask import Flask, render_template, Response, request
import numpy as np
import cv2

app = Flask(__name__)
frame_data = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_frame', methods=['POST'])
def update_frame():
    global frame_data
    frame_data = request.data
    return 'Frame received successfully', 200

def generate_frames():
    global frame_data
    while True:
        if frame_data is None:
            continue

        frame = np.frombuffer(frame_data, dtype=np.uint8)
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

        ret, jpeg = cv2.imencode('.jpg', frame)
        frame_bytes = jpeg.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

