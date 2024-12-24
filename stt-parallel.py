from src import NoiseHandler, VoiceEnhancer, VoiceSeperator, SpeakerDiarizer
from src import DataProcessor, AudioFileProcessor
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
    stt_file_name = "stt_parallel_" + args.file_name.split('.')[1].split('/')[-1] + '.json'
    print(f'stt: {stt_file_name}')
    audio_file_path = args.file_name    
    
    load_dotenv()
    openai_api_key = os.getenv('OPENAI_API')
    openai_client = OpenAI(api_key=openai_api_key)

    hf_api_key = os.getenv('HF_API')
    audio_p = AudioFileProcessor()
    noise_handler = NoiseHandler()
    voice_enhancer = VoiceEnhancer()
    voice_seperator = VoiceSeperator()

    speaker_diarizer = SpeakerDiarizer()
    speaker_diarizer.set_pyannotate(hf_api_key)
    stt_module = WhisperSTT(openai_api_key)
    stt_module.set_client()

    start = time.time()
    diar_result = speaker_diarizer.seperate_speakers(audio_p, audio_file_path, num_speakers=args.participant) 
    results = stt_module.process_segments_with_whisper_parallel(
                audio_p=audio_p,
                audio_file=args.file_name,
                segments=diar_result,
                chunk_size=10,
                max_workers=4
            )
    with open(os.path.join('./data', stt_file_name), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    print(f"모든 결과가 JSON 파일 '{os.path.join('./data', stt_file_name)}'로 저장되었습니다.")
    print(f"소요 시간: {time.time() - start}")

if __name__ == '__main__':
    cli_parser = argparse.ArgumentParser()
    cli_parser.add_argument('--output_path', type=str, default='./data/output')
    cli_parser.add_argument('--chunk_length', type=int, default=None)
    cli_parser.add_argument('--file_name', type=str, default=None) 
    cli_parser.add_argument('--participant', type=int, default=10)
    cli_args = cli_parser.parse_args()
    main(cli_args)