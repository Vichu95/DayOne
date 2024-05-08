from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

current_value = "Initial Value"

@app.route('/')
def index():
    return render_template('index.html', text="Value:", value=current_value)

@app.route('/update_value', methods=['POST'])
def update_value():
    global current_value
    new_value = request.form.get('new_value')
    if new_value:
        current_value = new_value
        return jsonify({'status': 'Value updated successfully', 'new_value': new_value})
    else:
        return jsonify({'status': 'Failed to update value'}), 400

if __name__ == '__main__':
    app.run(debug=True)

