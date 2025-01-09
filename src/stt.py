import io 
import os
from pydub import AudioSegment
from openai import OpenAI
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import tempfile
import re
import json

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

    def load_word_dictionary(self, json_path):
        with open(json_path, mode='r', encoding='utf-8') as file:
            self.word_dict = json.load(file)  # JSON 데이터를 한번만 로드
    
    def apply_word_dictionary(self, stt_text, word_dict):
        for incorrect_word, correct_word in word_dict.items():
            stt_text = stt_text.replace(incorrect_word, correct_word)
        return stt_text
    
    def apply_word_dictionary_regex(self, stt_text, word_dict):
        for incorrect_word, correct_word in word_dict.items():
            stt_text = re.sub(rf'\b{re.escape(incorrect_word)}\b', correct_word, stt_text)
        return stt_text
    
    def filter_stt_result(self, results):
        filtered_results = []
        prev_text = None
        for segment in results:
            text = segment['text'].strip()
            if text == prev_text:     # 이전 텍스트와 동일하면 제거
                continue
            prev_text = text
            filtered_results.append(segment)
        return filtered_results

    def process_segments_with_whisper(self, audio_p, audio_file, diar_results, db_stt_result_path, meeting_id, table_editor, openai_client):
        """
        화자 구간을 나눠 Whisper API에 바로 전달하여 텍스트 변환
        args:
            audio_file (str): 입력 오디오 파일 경로
            segments (List[Tuple[float, float, str]]): (시작 시간, 종료 시간, 화자) 세그먼트
        """
        if isinstance(audio_file, AudioSegment):
            whisper_audio = audio_file.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            audio_buffer = io.BytesIO()
            whisper_audio.export(audio_buffer, format="wav")
            audio_buffer.seek(0)
            audio_file = audio_buffer
        elif isinstance(audio_file, io.BytesIO):
            audio_file = audio_p.bytesio_to_tempfile(audio_file)
        
        exclude_word = ['뉴스', '구독', '시청']
        pattern = r'(^|\s|[^가-힣a-zA-Z0-9])(' + '|'.join(map(re.escape, exclude_word)) + r')($|\s|[^가-힣a-zA-Z0-9])'
        now = datetime.now()
        results = []
        audio = AudioSegment.from_file(audio_file)
        for idx, diar_result in enumerate(diar_results):
            diar_duration = diar_result['end'] - diar_result['start']
            start_time = now + timedelta(seconds=diar_result['start'])
            end_time = now + timedelta(seconds=diar_result['end'])
            if diar_duration < 0.1:
                print(f"Skipping segment {idx}: Duration too short ({diar_duration:.2f}s)")
                continue
            if diar_duration < 2:
                try:
                    start_ms = int(diar_result['start'] * 1000) - 1
                    end_ms = int(diar_result['end'] * 1000) + 1
                except:
                    start_ms = int(diar_result['start'] * 1000)
                    end_ms = int(diar_result['end'] * 1000)
            else:
                start_ms = int(diar_result['start'] * 1000)
                end_ms = int(diar_result['end'] * 1000)
            segment_audio = audio[start_ms:end_ms]
            segment_audio = segment_audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            
            audio_buffer = io.BytesIO()
            segment_audio.export(audio_buffer, format="wav")
            audio_buffer.seek(0)    # 파일 포인터를 처음으로 이동
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
                segment_audio.export(temp_audio_file.name, format="wav")
                with open(temp_audio_file.name, "rb") as audio_file:
                    transcription = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language='ko',
                        response_format='verbose_json'
                    )
            for segment in transcription.segments:
                if re.search(pattern, segment.text):
                    continue
                if segment.no_speech_prob < 0.7:
                    applied_text = self.apply_word_dictionary(segment.text, self.word_dict)
                    modified_text = openai_client.get_response(applied_text, role=openai_client.system_role, sub_role=openai_client.sub_role)
                    result = {
                        "speaker": diar_result['speaker'],
                        "start_time": start_time,
                        "end_time": end_time, 
                        "text": modified_text, 
                        "no_speech_prob": segment.no_speech_prob
                    }
                    results.append(result)
                    table_editor.edit_poc_conf_log_tb(task='insert', table_name='ibk_poc_conf_log', data=meeting_id, val=result)
            if idx == 0: 
                table_editor.edit_poc_conf_tb(task='update', table_name='ibk_poc_conf', data=meeting_id, val=db_stt_result_path)
        return results
    
    def transcribe_text(self, audio_p, audio_file, meeting_id=None, segment_id=None, table_editor=None):
        if isinstance(audio_file, AudioSegment):
            whisper_audio = audio_file.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            audio_buffer = io.BytesIO()
            whisper_audio.export(audio_buffer, format="wav")
            audio_buffer.seek(0)
            audio_file = audio_buffer
        elif isinstance(audio_file, io.BytesIO):
            audio_file = audio_p.bytesio_to_tempfile(audio_file)
        
        audio = AudioSegment.from_file(audio_file)    # 컨텍스트 매니저 제거
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
                    # timestamp_granularities=["segment"]
                )
        segments = transcription.segments
        # print(f'trans result: {transcription.segments}')   # id, avg_logprob, compression_ratio, end, no_speech_prob, seek, start, temperature (0.0), text, tokens
        if meeting_id == None:
            results = []
            for segment in segments:
                if segment.no_speech_prob < 0.9 and segment.avg_logprob > -2.0:
                    modified_text = self.apply_word_dictionary(segment.text, self.word_dict)
                    results.append({
                        "start_time": segment.start,
                        "end_time": segment.end, 
                        'text': modified_text.strip(),
                        'prob': segment.no_speech_prob,
                        'avg_logprob': segment.avg_logprob
                    })
            filtered_results = self.filter_stt_result(results)
            return filtered_results
        else:
            chunk_offset = segment_id * 270   # 청크의 시작 시간 오프셋 계산    
            for segment in segments:
                if segment.no_speech_prob < 0.9 and segment.avg_logprob > -2.0:
                    modified_text = self.apply_word_dictionary(segment.text, self.word_dict)
                    segment.start += chunk_offset 
                    segment.end += chunk_offset
                    stt_result = (segment.start, segment.end, segment.text)
                    table_editor.edit_poc_conf_log_tb(task='insert', table_name='ibk_poc_conf_log', data=meeting_id, val=stt_result)