from src import NoiseHandler, VoiceEnhancer, VoiceSeperator, SpeakerDiarizer
from src import DataProcessor
from src import WhisperSTT
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from pydub import AudioSegment
from openai import OpenAI
import argparse
import time
import json
import os
import gc

def main(args):
    file_name = "ibk-poc-meeting1.wav"
    audio_file_path = os.path.join(args.data_path, file_name)    
    speaker_info_pickle_path = os.path.join(args.output_path, 'speaker')

    load_dotenv()
    openai_api_key = os.getenv('OPENAI_API')
    print(openai_api_key)
    hf_api_key = os.getenv('HF_API')
    aai_api_key = os.getenv('AAI_API')

    openai_client = OpenAI(api_key=openai_api_key)
    data_p = DataProcessor()
    noise_handler = NoiseHandler()
    voice_enhancer = VoiceEnhancer()
    voice_seperator = VoiceSeperator()
    speaker_diarizer = SpeakerDiarizer()
    speaker_diarizer.set_pyannotate(hf_api_key)
    stt_module = WhisperSTT(openai_api_key)
    stt_module.set_client()
    audio_chunk = data_p.audio_chunk(audio_file_path, chunk_length=600, chunk_file_path=os.path.join(args.output_path, 'chunk'), chunk_file_name='stt-20241210-test1')

if __name__ == '__main__':
    cli_parser = argparse.ArgumentParser()
    cli_parser.add_argument('--data_path', type=str, default='./data')
    cli_parser.add_argument('--output_path', type=str, default='./data/output')
    cli_args = cli_parser.parse_args()
    main(cli_args)
