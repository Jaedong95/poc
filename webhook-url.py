from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/cori-webhook', methods=['POST'])
def handle_webhook():
    data = request.json
    print(data)
    # Process the data as needed
    return jsonify({'status': 'received'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)