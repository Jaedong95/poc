from flask import Flask, send_file, request, jsonify
import os

app = Flask(__name__)

@app.route('/stt', methods=['GET'])
def get_audio_file():
    # 오디오 파일의 전체 경로 확인
    # print(f'{os.path.join(file_path, file_name}')
    print('hello')
    file_path = '/ibk/meeting_records/'
    file_name = request.args.get('audio_file_name')
    try:
        return send_file(os.path.join(file_path, file_name), mimetype='audio/wav')
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/stt/result', methods=['POST'])
def webhook():
    data = request.json
    print("Webhook received:", data)
    # file_path = '/home/jsh0630/meeting_records/'
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=True)
~                                                  