from src import NoiseHandler, VoiceEnhancer, VoiceSeperator, SpeakerDiarizer
from dotenv import load_dotenv
from openai import OpenAI
import json 
import os

'''
with open('./data/stt_lufs_norm_ibk-poc-meeting_20241220.json', mode='r', encoding='utf-8') as file:
    stt_result = json.load(file)

processed_result = []
for result in stt_result:
    processed_result.append((result['speaker'], result['text']))

json_data = [{'speaker': speaker, 'text': text} for speaker, text in processed_result]
output_file = "stt_lufs_norm_ibk-poc-meeting_20241220o.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(json_data, f, ensure_ascii=False, indent=4)'''


load_dotenv()
openai_api_key = os.getenv('OPENAI_API')
openai_client = OpenAI(api_key=openai_api_key)

hf_api_key = os.getenv('HF_API')
speaker_diarizer = SpeakerDiarizer()
speaker_diarizer.set_pyannotate(hf_api_key)
    
with open('./data/diar_lufs_norm_ibk-poc-meeting_20241220.json', mode='r', encoding='utf-8') as file:
    diar_result = json.load(file)

speaker_diarizer.calc_speak_duration(diar_result, 'SPEAKER_00')

