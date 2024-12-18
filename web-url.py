from flask import Flask, send_file, request, jsonify

app = Flask(__name__)

@app.route('/stt-20241210-test1_0.wav', methods=['GET'])
def get_audio_file():
    # 오디오 파일의 전체 경로 확인
    file_path = './data/output/chunk/stt-20241210-test1_0.wav'
    try:
        return send_file(file_path, mimetype='audio/wav')
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/cori-webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Webhook received:", data)
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)