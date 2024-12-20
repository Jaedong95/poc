from src import NoiseHandler, VoiceEnhancer, VoiceSeperator, SpeakerDiarizer
from src import DataProcessor
from src import WhisperSTT
from flask import Flask, send_file, request, jsonify
from dotenv import load_dotenv
from pydub import AudioSegment
from openai import OpenAI
import argparse
import time
import json
import os
import gc

app = Flask(__name__)

@app.route('/stt/', methods=['GET'])
def get_audio_file():
    file_path = '/ibk/meeting_records/'
    file_name = request.args.get('audio_file_name')
    '''noise_handler = NoiseHandler()
    nnnoise_audio = noise_handler.remove_background_noise(audio_file_path, prop_decrease=0.3)
    filtered_chunk = noise_handler.filter_audio_with_ffmpeg(nnnoise_audio, high_cutoff=150, low_cutoff=5000)'''
    try:
        return send_file(os.path.join(file_path, file_name), mimetype='audio/wav')
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/stt/result', methods=['POST'])
def webhook():
    '''
    data: {
        "jobId": "bd7e97c9-0742-4a19-bd5a-9df519ce8c74",
        "status": "succeeded",
        "output": {
            "diarization": [
                { "start": 1.2,
                  "end": 3.4,
                  "speaker": "SPEAKER_01" },
                ...
            ]
        }
    }
    '''
    data_p = DataProcessor()
    data = request.json
    diar_result = data['output']['diarization']
    result = stt_module.process_segments_with_whisper(data_p, filtered_chunk, diar_result)

    print(f"test: {data['output']['diarization'][0]}, len: {len(data['output']['diarization'])}")
    return result
    # return jsonify({"status": "success"}), 200

@app.post('/run')
def run_python_code(data):
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=True)