from pydub import AudioSegment
from openai import OpenAI
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import io
import os
import json
import logging

class STTModule:
    def __init__(self, openai_api_key=None, ms_api=None):
        self.openai_api_key = openai_api_key
        self.ms_api = ms_api 
    
    @abstractmethod
    def set_client(self):
        pass

    @abstractmethod
    def convert_text_to_speech(self, audio_path, save_path):
        pass 


class WhisperSTT(STTModule):
    def __init__(self, openai_api_key):
        super().__init__(openai_api_key=openai_api_key)
    
    def set_client(self):
        self.openai_client = OpenAI(api_key=self.openai_api_key)

    def load_word_dictionary(self, json_path):
        with open(json_path, mode='r', encoding='utf-8') as file:
            self.word_dict = json.load(file)
    
    def apply_word_dictionary(self, stt_text, word_dict):
        for incorrect_word, correct_word in word_dict.items():
            stt_text = stt_text.replace(incorrect_word, correct_word)
        return stt_text
    
    def apply_word_dictionary_regex(self, stt_text, word_dict):
        for incorrect_word, correct_word in word_dict.items():
            stt_text = re.sub(rf'\b{re.escape(incorrect_word)}\b', correct_word, stt_text)
        return stt_text

    def transcribe_text(self, audio_p, audio_file):
        if isinstance(audio_file, AudioSegment):
            whisper_audio = audio_file.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            audio_buffer = io.BytesIO()
            whisper_audio.export(audio_buffer, format="wav")
            audio_buffer.seek(0)
            audio_file = audio_buffer
        elif isinstance(audio_file, io.BytesIO):
            audio_file = audio_p.bytesio_to_tempfile(audio_file)
        
        audio = AudioSegment.from_file(audio_file)  # 컨텍스트 매니저 제거
        whisper_audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        self.load_word_dictionary(os.path.join('./config', 'word_dict.json'))
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
            whisper_audio.export(temp_audio_file.name, format="wav")
            with open(temp_audio_file.name, "rb") as audio_file:
                transcription = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language='ko',
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
        segments = transcription.segments
        print(f'trans result: {transcription.segments}')   # id, avg_logprob, compression_ratio, end, no_speech_prob, seek, start, temperature (0.0), text, tokens
        results = []
        for segment in segments:
            if segment.no_speech_prob < 0.9:
                modified_text = self.apply_word_dictionary(segment.text, self.word_dict)
                results.append({
                    'start_time': round(segment.start, 2),
                    'end_time': round(segment.end, 2),
                    'text': segment.text
                })
        return results