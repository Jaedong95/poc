import requests
import time 

# PyAnnote API 설정
api_token = "sk_b52152a1619c41e6835c2334cc443cf6"
api_url = "https://api.pyannote.ai/v1/diarize"
file_url = "http://localhost:5000/ibk-poc-meeting1.wav"
webhook_url = "http://localhost:5000/cori-webhook"

# 오디오 파일 설정
audio_file_path = "./data/output/chunk/stt-20241210-test1_0.wav"
headers = {
    "Authorization": f"Bearer {api_token}"
}

start = time.time()
# 오디오 파일 업로드 및 API 호출
with open(audio_file_path, "rb") as audio_file:
    files = {"audio": audio_file}
    response = requests.post(api_url, headers=headers, files=files)

# 결과 확인
if response.status_code == 200:
    diarization_result = response.json()
    print("Diarization Result:", diarization_result)
else:
    print(f"Error: {response.status_code}, {response.text}")
print(f'소요 시간: {time.time() - start}초')