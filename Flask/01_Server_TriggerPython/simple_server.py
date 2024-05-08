import os
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
   return render_template('index.html')

@app.route('/open_link')
def open_link():
   # Code to open a link on your laptop
   return 'Link opened successfully'

@app.route('/run_script')
def run_script():
   # Code to run a script on your laptop
   os.system("python helloworld.py")
   return 'Script executed successfully'

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=5000)
