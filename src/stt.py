from pydub import AudioSegment
from openai import OpenAI
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import io

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
        # print(f'test: {self.openai_api_key}')
        self.openai_client = OpenAI(api_key=self.openai_api_key)

    def process_single_segment(self, audio, segment, include_word):
        """
        개별 세그먼트를 Whisper API로 처리
        """
        try:
            segment_duration = segment['end'] - segment['start']
            start_ms, end_ms = int(segment['start'] * 1000), int(segment['end'] * 1000)
            segment_audio = audio[start_ms:end_ms]
            segment_audio = segment_audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)

            # Whisper API 호출
            audio_buffer = io.BytesIO()
            segment_audio.export(audio_buffer, format="wav")
            audio_buffer.seek(0)

            transcription = self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_buffer,
                language='ko'
            )

            transcription_text = transcription.text.strip()
            if segment_duration < 2 and (len(transcription_text) < 4 or not include_word.intersection(transcription_text.split())):
                logging.info(f"Skipping segment: Text too short or irrelevant")
                return None

            if not transcription_text:
                return None

            return {
                "speaker": segment["speaker"],
                "start_time": round(segment["start"], 2),
                "end_time": round(segment["end"], 2),
                "text": transcription_text
            }
        except Exception as e:
            logging.error(f"Error processing segment for Speaker {segment['speaker']}: {e}")
            return None

    def process_segments_with_whisper_parallel(self, audio_p, audio_file, segments, chunk_size=10, max_workers=4):
        """
        화자 구간을 나눠 Whisper API에 병렬 처리로 텍스트 변환
        """
        if isinstance(audio_file, io.BytesIO):
            audio_file = audio_p.bytesio_to_tempfile(audio_file)

        results = []
        include_word = {'네', '아니오'}
        audio = AudioSegment.from_file(audio_file)

        # 청크 단위로 세그먼트 분할
        chunks = [segments[i:i + chunk_size] for i in range(0, len(segments), chunk_size)]
        with ThreadPoolExecutor(max_workers=max_workers) as executor:   # 병렬 처리
            future_to_chunk = {
                executor.submit(self.process_chunk, audio, chunk, include_word): chunk for chunk in chunks
            }
            for future in as_completed(future_to_chunk):
                chunk_results = future.result()
                if chunk_results:
                    results.extend(chunk_results)
        return results

    def process_chunk(self, audio, chunk, include_word):
        """
        각 청크를 처리하는 함수
        """
        chunk_results = []
        for segment in chunk:
            result = self.process_single_segment(audio, segment, include_word)
            if result:
                chunk_results.append(result)
        return chunk_results

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

            start_ms = int(segment['start'] * 1000)
            end_ms = int(segment['end'] * 1000)
            segment_audio = audio[start_ms:end_ms]
            segment_audio = segment_audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            
            audio_buffer = io.BytesIO()
            segment_audio.export(audio_buffer, format="wav")
            audio_buffer.seek(0)    # 파일 포인터를 처음으로 이동
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
                    segment_audio.export(temp_audio_file.name, format="wav")
                    with open(temp_audio_file.name, "rb") as audio_file:
                        transcription = self.openai_client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            language='ko',
                        )
                    if transcription.text == '':
                        continue
                    results.append({
                        "speaker": segment["speaker"],
                        "start_time": round(segment["start"], 2),
                        "end_time": round(segment["end"], 2),
                        "text": transcription.text
                    })
            except Exception as e:
                print(f"Error processing segment {i} for Speaker {segment['speaker']}: {e}")
        return results