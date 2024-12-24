from abc import ABC, abstractmethod
from pydub import AudioSegment
from openai import OpenAI
import tempfile
import json
import re
import io
import os

class STTModule:
    def __init__(self, openai_api_key=None, ms_api_key=None):
        self.openai_api_key = openai_api_key
        self.ms_api_key = ms_api_key 
    
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

    def load_word_dictionary(json_path):
        with open(json_path, mode='r', encoding='utf-8') as file:
            return json.load(file)

    def apply_word_dictionary_regex(stt_text, word_dict):
        for incorrect_word, correct_word in word_dict.items():
            stt_text = re.sub(rf'\b{re.escape(incorrect_word)}\b', correct_word, stt_text)
        return stt_text

    def filter_outlier_data(self, transcription, segment_duration, include_word): 
        if segment_duration < 2 or transcription.text == '':
            tmp = transcription.text.replace(",. ", "")
            if len(tmp) >= 4:        
                logger.info(f"Wrong generation sentence maybe ..  ex) MBC 뉴스 이덕영입니다. ({segment_duration:.2f}s)")
                return False
            elif not any(word in transcription.text for word in include_word):
                logger.info(f"Wrong generation short sentence maybe ..  ex) 고마워 ({segment_duration:.2f}s)")
                return False
        return True

    def transcribe_data(self, audio_data):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
            try:
                audio_data.export(temp_audio_file.name, format="wav")
                with open(temp_audio_file.name, "rb") as audio_file:
                    transcription = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language='ko',
                        # prompt="이 대화는 이뤄지는 한국어 대화입니다."
                    )
            finally:
                os.remove(temp_audio_file.name)
        return transcription

    def process_segment(self, audio_file, segment, include_word):
        segment_duration = segment['end'] - segment['start']
        if segment_duration < 0.1:
            return None 

        audio = AudioSegment.from_file(audio_file)
        start_ms = int(segment['start'] * 1000); end_ms = int(segment['end'] * 1000)
        segment_audio = audio[start_ms:end_ms].set_frame_rate(16000).set_channels(1).set_sample_width(2)
        audio_buffer = io.BytesIO()
        segment_audio.export(audio_buffer, format="wav")
        audio_buffer.seek(0)

        try:
            transcription = self.transcribe_data(audio_buffer)
            if self.filter_outlier_data(transcription, segment_duration, include_word):
                return {
                    "speaker": segment["speaker"],
                    "start_time": round(segment["start"], 2),
                    "end_time": round(segment["end"], 2),
                    "text": transcription.text
                }
        except Exception as e:
            print(f"Error processing segment: {e}")
        return None

    def process_segments_in_parallel(self, audio_file, segments, inclue_word=['네','아니오']):
        results = []
        with ProcessPoolExecutor() as executor:
            future_to_segment = {
                executor.submit(self.process_segment, audio_file, segment, include_word): segment for segment in segments
            }
            for future in as_completed(future_to_segment):
                segment_result = future.result()
                if segment_result:
                    results.append(segment_result)
        return results

    def process_segments_with_whisper(self, data_p, audio_file, segments):
        """
        화자 구간을 나눠 Whisper API에 바로 전달하여 텍스트 변환
        args:
            audio_file (str): 입력 오디오 파일 경로
            segments (List[Tuple[float, float, str]]): (시작 시간, 종료 시간, 화자) 세그먼트
        """
        if isinstance(audio_file, io.BytesIO):   # 입력 데이터 형식 확인 및 변환
            audio_file = data_p.bytesio_to_tempfile(audio_file)
        
        results = []
        include_word = ['네', '아니오']
        audio = AudioSegment.from_file(audio_file)
        for i, segment in enumerate(segments):
            segment_duration = segment['end'] - segment['start']
            if segment_duration < 0.1:
                print(f"Skipping segment {i}: Duration too short ({segment_duration:.2f}s)")
                continue
            start_ms = int(segment['start'] * 1000); end_ms = int(segment['end'] * 1000)
            segment_audio = audio[start_ms:end_ms].set_frame_rate(16000).set_channels(1).set_sample_width(2)
            
            audio_buffer = io.BytesIO()
            segment_audio.export(audio_buffer, format="wav")
            audio_buffer.seek(0)    # 파일 포인터를 처음으로 이동
            try:
                transcription = self.transcribe_data(audio_buffer)
                if not self.filter_outlier_data(transcription, segment_duration, include_word):
                    results.append({
                        "speaker": segment["speaker"],
                        "start_time": round(segment["start"], 2),
                        "end_time": round(segment["end"], 2),
                        "text": transcription.text
                    })
            except Exception as e:
                print(f"Error processing segment {i} for Speaker {segment['speaker']}: {e}")
        return results