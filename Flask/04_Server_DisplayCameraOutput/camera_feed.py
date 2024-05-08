import cv2
import requests
import numpy as np

def capture_camera_and_send():
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame")
            break
		
        cv2.imshow('Camera Feed', frame)  # Display the frame
        if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
            break
            
        # Encode the frame as JPEG
        _, jpeg = cv2.imencode('.jpg', frame)
        frame_bytes = jpeg.tobytes()

        # Send the frame to the Flask server
        try:
            response = requests.post('http://127.0.0.1:5000/update_frame', data=frame_bytes)
            if response.status_code != 200:
                print("Failed to send frame to server")
        except requests.exceptions.RequestException as e:
            print("Error sending frame to server:", e)

    cap.release()

if __name__ == '__main__':
    capture_camera_and_send()

