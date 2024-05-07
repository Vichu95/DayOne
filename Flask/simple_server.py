from flask import Flask

import os
 
app = Flask(__name__)

@app.route('/trigger_action')
def trigger_action():
    # Execute action based on the received request
    # For example, open a link or execute a command
    # Replace this with your desired action
    
    
    # running other file using run()
    os.system("python helloworld.py")
    
    
    
    return 'Action triggered successfully'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Run the server on all available interfaces
