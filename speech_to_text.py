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
    stt_file_name = "stt_" + args.file_name.split('.')[0] + '.json'
    audio_file_path = args.file_name    
    
    load_dotenv()
    openai_api_key = os.getenv('OPENAI_API')
    openai_client = OpenAI(api_key=openai_api_key)

    hf_api_key = os.getenv('HF_API')
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
    if args.chunk_length == None:
        nnnoise_audio = noise_handler.remove_background_noise(audio_file_path, prop_decrease=0.3)
        filtered_chunk = noise_handler.filter_audio_with_ffmpeg(nnnoise_audio, high_cutoff=150, low_cutoff=5000)
        diar_result = speaker_diarizer.seperate_speakers(filtered_chunk, num_speakers=args.participant)     
        result = stt_module.process_segments_with_whisper(speaker_diarizer, filtered_chunk, diar_result)
        filtered_chunk.close()
        gc.collect()

        with open(stt_file_name, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        print(f"모든 결과가 JSON 파일 '{stt_file_name}'로 저장되었습니다.")
    else:
        audio_chunk = data_p.audio_chunk(audio_file_path, chunk_length=args.chunk_length)
        for idx, chunk in enumerate(audio_chunk):
            cstt_file_name = os.path.join(args.output_path, stt_file_name.split('.')[0] + f'_{idx}.json')
            nnnoise_chunk = noise_handler.remove_background_noise(chunk, prop_decrease=0.5)
            filtered_chunk = noise_handler.filter_audio_with_ffmpeg(nnnoise_chunk, high_cutoff=150, low_cutoff=5000)
            # nnnoise_chunk.close()
            print(f'오디오 주파수 필터링: {time.time() - start}')
            # emphasized_chunk = voice_enhancer.emphasize_nearby_voice(filtered_chunk)

            diar_result = speaker_diarizer.seperate_speakers(filtered_chunk, num_speakers=args.participant)     
            result = stt_module.process_segments_with_whisper(speaker_diarizer, filtered_chunk, diar_result)
            filtered_chunk.close()
            gc.collect()

            with open(cstt_file_name, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
            print(f"모든 결과가 JSON 파일 '{cstt_file_name}'로 저장되었습니다.")


if __name__ == '__main__':
    cli_parser = argparse.ArgumentParser()
    cli_parser.add_argument('--output_path', type=str, default='./data/output')
    cli_parser.add_argument('--chunk_length', type=int, default=None)
    cli_parser.add_argument('--file_name', type=str, default=None) 
    cli_parser.add_argument('--participant', type=int, default=5)
    cli_args = cli_parser.parse_args()
    main(cli_args)