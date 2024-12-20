from src import NoiseHandler, VoiceEnhancer, VoiceSeperator, SpeakerDiarizer, AudioFileProcessor
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
    data_path = "./data/ibk-poc-call-meeting_20241220.m4a"
    audio_file_path = args.file_name    
    
    load_dotenv()
    audio_p = AudioFileProcessor()
    audio_p.m4a_to_wav(data_path)

if __name__ == '__main__':
    cli_parser = argparse.ArgumentParser()
    cli_parser.add_argument('--output_path', type=str, default='./data/output')
    cli_parser.add_argument('--chunk_length', type=int, default=None)
    cli_parser.add_argument('--file_name', type=str, default=None) 
    cli_args = cli_parser.parse_args()
    main(cli_args)