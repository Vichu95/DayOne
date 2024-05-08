from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

triggered_value = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/trigger_value', methods=['POST'])
def trigger_value():
    global triggered_value
    data = request.json  # Extract JSON data from the request
    if data:
        value = data.get('value')
        print("Received value:", value)  # Log the received value
        triggered_value = value
        return 'Value triggered successfully' , 200
    else:
        return 'No data received', 400  # Return an error response if no data is received

@app.route('/get_triggered_value', methods=['GET'])
def get_triggered_value():
    global triggered_value
    return jsonify({'triggered_value': triggered_value})

if __name__ == '__main__':
    app.run(debug=True)

