from src import NoiseHandler, VoiceEnhancer, VoiceSeperator, SpeakerDiarizer
from src import DataProcessor, AudioFileProcessor
from src import WhisperSTT
from dotenv import load_dotenv
import os 
import openai
from openai import OpenAI

audio_file_path = "./data/output/chunk/stt_chunk_lufs_norm_ibk-poc-meeting_20241220_3.wav"
audio_file = open(audio_file_path, "rb")
load_dotenv()
openai_api_key = os.getenv('OPENAI_API')
openai_client = OpenAI(api_key=openai_api_key)

transcription = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language='ko',
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
#print(f"trans result: {transcription.segments}")
for segment in transcription.segments:
    if segment.no_speech_prob < 0.9:  # 음성이 있다고 판단되는 경우
        print(f"Start: {segment.start}, End: {segment.end}, Text: '{segment.text}, prob: {segment.no_speech_prob}'")
    else:
        print(f"Skipping segment: No speech detected (probability: {segment.no_speech_prob})")
        print(segment.text)