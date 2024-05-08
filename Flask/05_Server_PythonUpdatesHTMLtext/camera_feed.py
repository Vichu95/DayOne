import requests
import time

def send_value():
    while True:
        try:
            response = requests.post('http://127.0.0.1:5000/update_value', data={'new_value': 'New Value'})
            if response.status_code == 200:
                print("Value updated successfully")
            else:
                print("Failed to update value python")
        except requests.exceptions.RequestException as e:
            print("Error sending request:", e)
        
        time.sleep(5)  # Send request every 5 seconds

if __name__ == '__main__':
    send_value()

