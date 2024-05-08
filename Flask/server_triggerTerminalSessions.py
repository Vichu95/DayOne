from flask import Flask, render_template
import os
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_session')
def start_session():
    # Start a new tmux session with your command
    os.system("tmux new-session -d -s my_session_name 'top'")
    return 'Session started successfully'

@app.route('/stop_session')
def stop_session():
    # Kill the tmux session
    os.system("tmux kill-session -t my_session_name")
    return 'Session stopped successfully'

@app.route('/status')
def session_status():
    # Check if the tmux session is running
    status = os.system("tmux has-session -t my_session_name")
    if status == 0:
        return 'Session is running'
    else:
        return 'Session is not running'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

