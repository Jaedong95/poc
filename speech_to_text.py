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

    # voice_seperator.seperate_vocals_with_umix(audio_file_path, sep_file_path)   # 음성, 베이스, 건반 등 소리 분리  - 자원상 문제로 일단 스킵    
    start = time.time()
    audio_chunk = data_p.audio_chunk(audio_file_path, chunk_length=600)
    
    for idx, chunk in enumerate(audio_chunk):
        file_name = os.path.join(args.output_path, f'stt_results_20241210_1_{idx}.json')
        speaker_info_pickle = f'sep-speaker_20241210_1-{idx}.pickle'
        nnnoise_chunk = noise_handler.remove_background_noise(chunk, prop_decrease=0.5)
        print(f'노이즈 제거: {time.time() - start}')
        filtered_chunk = noise_handler.filter_audio_with_ffmpeg(chunk, high_cutoff=150, low_cutoff=5000)
        # nnnoise_chunk.close()
        print(f'오디오 주파수 필터링: {time.time() - start}')
        # emphasized_chunk = voice_enhancer.emphasize_nearby_voice(filtered_chunk)
        
        # print(f'근접 보이스 강조: {time.time() - start}', end='\n\n')
        diar_result = speaker_diarizer.seperate_speakers(filtered_chunk, speaker_info_pickle_path, speaker_info_pickle, local=True)     
        # print(diar_result)  
        result = stt_module.process_segments_with_whisper(speaker_diarizer, filtered_chunk, diar_result)
        print(result)
        filtered_chunk.close()
        gc.collect()

        if file_name: 
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
            print(f"모든 결과가 JSON 파일 '{file_name}'로 저장되었습니다.")
        

if __name__ == '__main__':
    cli_parser = argparse.ArgumentParser()
    cli_parser.add_argument('--data_path', type=str, default='./data')
    cli_parser.add_argument('--output_path', type=str, default='./data/output')
    cli_args = cli_parser.parse_args()
    main(cli_args)