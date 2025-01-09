from src import NoiseHandler, VoiceEnhancer, VoiceSeperator, SpeakerDiarizer
from src import AudioFileProcessor, DataProcessor
from src import WhisperSTT, LLMOpenAI
from pydub.silence import detect_nonsilent
from dotenv import load_dotenv
from pydub import AudioSegment
from openai import OpenAI
import tempfile
import argparse
import time
import json
import os
import gc


def main(args):
    stt_file_name = "stt_" + args.file_name.split('.')[1].split('/')[-1] + '.json'
    diar_file_name = "diar_" + args.file_name.split('.')[1].split('/')[-1] + '.json'
    audio_file_path = args.file_name    
    
    load_dotenv()
    openai_api_key = os.getenv('OPENAI_API')
    openai_client = OpenAI(api_key=openai_api_key)

    hf_api_key = os.getenv('HF_API')
    data_p = DataProcessor()

    speaker_diarizer = SpeakerDiarizer()
    speaker_diarizer.set_pyannotate(hf_api_key)
    stt_module = WhisperSTT(openai_api_key)
    stt_module.set_client()
    stt_module.load_word_dictionary('./config/word_dict.json')

    start = time.time()
    diar_file_path = os.path.join('meeting_records', 'wav', audio_file_path.split('/')[-1])
    
    with open(os.path.join('./meeting_records', 'diar', diar_file_name), "r", encoding="utf-8") as f:
       diar_result = json.load(f)
    
    new_result = speaker_diarizer.rename_speaker_test(diar_result, args.participant)
    with open(os.path.join('./meeting_records', 'diar', 'test.json'), "w", encoding="utf-8") as f:
        json.dump(new_result, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    cli_parser = argparse.ArgumentParser()
    cli_parser.add_argument('--output_path', type=str, default='./meeting_records/output')
    cli_parser.add_argument('--chunk_length', type=int, default=None)
    cli_parser.add_argument('--file_name', type=str, default=None) 
    cli_parser.add_argument('--participant', type=int, default=None)
    cli_args = cli_parser.parse_args()
    main(cli_args)