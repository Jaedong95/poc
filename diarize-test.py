import requests

# PyAnnote API 설정
api_token = "pab0abbd"
api_url = "https://api.pyannote.ai/v1/diarize"

# 오디오 파일 설정
audio_file_path = "./data/output/chunk/stt-20241212-test2_0.wav"
headers = {
    "Authorization": f"Bearer {api_token}"
}

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