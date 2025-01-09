from flask import Flask, send_file, request, jsonify, Response
from src import SpeakerDiarizer, AudioFileProcessor, TimeProcessor, WhisperSTT
from src import DBConnection, TableEditor, PostgresDB
from src import LLMOpenAI
from dotenv import load_dotenv
from datetime import datetime
import requests
import base64
import json
import io
import os


app = Flask(__name__)

load_dotenv()
openai_api_key = os.getenv('OPENAI_API')
with open(os.path.join('./config', 'db_config.json')) as f:
    db_config = json.load(f)

db_conn = DBConnection(db_config)
db_conn.connect()
postgres = PostgresDB(db_conn)
table_editor = TableEditor(db_conn)

diar_module = SpeakerDiarizer()
audio_p = AudioFileProcessor()
time_p = TimeProcessor()

stt_module = WhisperSTT(openai_api_key)
stt_module.set_client()
stt_module.load_word_dictionary('/ibk/config/word_dict.json')
'''with open(os.path.join('./config', 'llm_config.json')) as f:
    llm_config = json.load(f)
openai_client = LLMOpenAI(llm_config, openai_api_key)
openai_client.set_generation_config()
openai_client.set_grammer_guideline()'''

def custom_json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable") 

def map_speaker_with_nested_check(meeting_id, stt_result, diar_segments):
    """ stt_result: conv_id, start_time, end_time, text, conf_id """
    conv_id = stt_result[0]
    print(f'stt_segment: {stt_result}')
    stt_start, stt_end = stt_result[2], stt_result[3]
    
    candidates = []
    for diar_seg in diar_segments:   # STT 결과값과 겹치는 Diar 구간 탐색 
        diar_start, diar_end = diar_seg['start'], diar_seg['end']
        if stt_start <= diar_end and stt_end >= diar_start:  # 겹침 조건
            candidates.append(diar_seg)
    
    if not candidates:
        print("No overlapping segments found.")
        return    # DB 업데이트 x 

    for candidate in candidates:
        diar_start, diar_end = candidate['start'], candidate['end']
        nested_segments = [     #  Diar 구간 내에 또 다른 구간 탐색 (0~19 -> 13~14)
            seg for seg in diar_segments
            if seg['start'] >= diar_start and seg['end'] <= diar_end and seg != candidate
        ]
        if nested_segments:   # 또 다른 발화가 있을 때 
            for nested in nested_segments:
                if time_p.is_similar(nested, stt_result):
                    updated_result = (conv_id, nested['speaker'])
                    table_editor.edit_poc_conf_log_tb('update', 'ibk_poc_conf_log', data=meeting_id, val=updated_result)
                    return 
        
        # 또 다른 발화가 없을 때 (겹치는 후보군들만 탐색)
        max_overlap = 0
        for diar_seg in candidates:
            overlap_start = max(stt_start, diar_seg['start'])
            overlap_end = min(stt_end, diar_seg['end'])
            overlap_duration = max(0, overlap_end - overlap_start)
            if overlap_duration > max_overlap:
                max_overlap = overlap_duration
                updated_result = (conv_id, diar_seg['speaker'])
                table_editor.edit_poc_conf_log_tb('update', 'ibk_poc_conf_log', data=meeting_id, val=updated_result)
                return 
        return 

@app.route('/stt/', methods=['GET'])
def get_audio_file():
    file_name = request.args.get('audio_file_name')
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
    print(f'2: {participant_cnt}')
    data = request.json
    diar_result = data['output']['diarization']
    filtered_result = diar_module.rename_speaker(diar_result, participant_cnt)
    with open(os.path.join(file_path, audio_file_name.split('.')[0] + '.json'), 'w', encoding='utf-8') as f:
        json.dump(filtered_result, f, ensure_ascii=False, indent=4)
    print(meeting_id)
    stt_results = postgres.get_conf_log_data(meeting_id)
    for stt_result in stt_results: 
        map_speaker_with_nested_check(meeting_id, stt_result, filtered_result)
    return jsonify({"status": "received"}), 200


@app.post('/run-stt')
def run_stt_code():
    global stt_result_path      # /ibk/meeting_records/stt_result/ibk-poc-meeting1.json
    global db_stt_result_path   
    global audio_p
    global db_conn
    global table_editor
    global db_config

    data = request.get_json()
    meeting_id = data['meeting_Id']
    file_idx = data['section_Id']
    encoded_audio = data['audio_file']
    decoded_audio = base64.b64decode(encoded_audio)
    audio_file = io.BytesIO(decoded_audio)

    stt_module.transcribe_text(audio_p, audio_file, meeting_id, file_idx, table_editor)
    return jsonify({"status": "received"}), 200


@app.post('/run')
def run_python_code():
    global participant_cnt
    global meeting_id
    global file_path    # /ibk/meeting_records
    global diar_module
    global new_file_name     # /ibk/meeting_records/ibk-poc-meeting1.wav
    global audio_file_name     # ibk-poc-meeting1.wav
    global stt_result_path
    global db_stt_result_path
    global postgres

    #load_dotenv()
    data = request.get_json()
    pyannot_api_key = os.getenv('PA_API')
    
    file_path = '/ibk/meeting_records/'
    file_name = data['file_name']     # /ibk/meeting_records/ibk-poc-meeting1.wav
    print(f'file_path: {file_path}')
    print(f'file_name: {file_name}')
    participant_cnt = data['participant']
    new_file_name = file_path + file_name.split('/')[-1]
    audio_file_name = new_file_name.split('/')[-1]
    print(f'audio_file_name: {audio_file_name}')
    meeting_id = int(audio_file_name.split('_')[1])
    pyannotate_url = "https://api.pyannote.ai/v1/diarize"
    file_url = f"https://ibkpoc.fingerservice.co.kr/stt/?audio_file_name={audio_file_name}"
    webhook_url = "https://ibkpoc.fingerservice.co.kr/stt/result"
    headers = {
        "Authorization": f"Bearer {pyannot_api_key}"
    }
    data = {
        "webhook": webhook_url,
        "url": file_url
    }
    print(f'1: global_cnt: {participant_cnt}')

    stt_result_path = '/ibk/meeting_records/stt_result/' + audio_file_name.replace('.wav', '.json')
    db_stt_result_path = '/home/jsh0630/meeting_records/stt_result/' + audio_file_name.replace('.wav', '.json')

    external_response = requests.post(pyannotate_url, headers=headers, json=data)
    flask_response = Response(
        response=external_response.content,   # 응답 본문
        status=external_response.status_code,    # 상태 코드
        content_type=external_response.headers.get('Content-Type')  # Content-Type 헤더
    )
    return flask_response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=True)
