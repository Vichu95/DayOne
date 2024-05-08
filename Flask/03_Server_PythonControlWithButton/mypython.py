import requests
import time

def receive_triggered_value():
    while True:
    
    	try:
       		response = requests.get('http://127.0.0.1:5000/get_triggered_value')
       		data = response.json()
       		
       		print(data)
       		triggered_value = data.get('triggered_value')
       		print("Triggered Value:", triggered_value)
       		time.sleep(1)
    	except requests.ConnectionError:
       		print("Connection error: Failed to connect to the server:",requests.ConnectionError)	
    	

if __name__ == '__main__':
    receive_triggered_value()

