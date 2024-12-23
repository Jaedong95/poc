'''
SPEAKER
'''

import json
from collections import Counter

# JSON 데이터
stt_data = [
    {
        "speaker": "SPEAKER_04",
        "start_time": 0.54,
        "end_time": 3.19,
        "text": "네, 안 빼기로 했어요. 절대 안 뺏겼습니다."
    },
    {
        "speaker": "SPEAKER_04",
        "start_time": 4.11,
        "end_time": 8.86,
        "text": "그리고 여기 보시면 옆에 NCG PTS 라고 적혀있는데"
    },
    {
        "speaker": "SPEAKER_04",
        "start_time": 9.5,
        "end_time": 13.85,
        "text": "이쪽에다가 그거를 넘겼으면 좋겠대요 재무제표가"
    },
    {
        "speaker": "SPEAKER_04",
        "start_time": 14.48,
        "end_time": 18.95,
        "text": "이거 치킨티스 아닌 것 같다. 네 절대 아닙니다."
    },
    {
        "speaker": "SPEAKER_04",
        "start_time": 25.39,
        "end_time": 30.54,
        "text": "예를 들어서 재무조표 들어가면 눌러서 재무조표 들어가게 되는거고 그런식으로"
    },
    {
        "speaker": "SPEAKER_02",
        "start_time": 29.53,
        "end_time": 37.12,
        "text": "그런식으로"
    },
    {
        "speaker": "SPEAKER_04",
        "start_time": 36.94,
        "end_time": 53.63,
        "text": "이 관리자 페이지 같은 경우는 별도로 아예 그 관리자들이 볼 수 있게 모니터링 할 수 있는거잖아요. 히스토리 볼 수 있는거. 그거를 원하는 것 같아요. 그래서 이 관리자 페이지로 할지 아니면 이걸 없애버리고 아예 별도로 UI를 따로 봐가지고 해야 할지는"
    },
    {
        "speaker": "SPEAKER_04",
        "start_time": 57.98,
        "end_time": 74.97,
        "text": "관리자 같은 경우에는 계획에 나온 게 없는데 여기서 지금 원하는 거 보니까 주식 모니터링 같은 거 있잖아요 그거 같은 경우는 모니터링 결과물들 나온 거 목록별로 해서 다운로드하고 과거네이터들 그런 게 가능한지 모르겠어요"
    },
    {
        "speaker": "SPEAKER_02",
        "start_time": 74.8,
        "end_time": 87.36,
        "text": "우선은 여기부터 가면 두 번째 있잖아요. 일반적인 금융관련과 맞아요. 이거도 얘기하시더라고요. 저희 계약금이 5개인데."
    },
    {
        "speaker": "SPEAKER_04",
        "start_time": 90.82,
        "end_time": 97.03,
        "text": "확인을 해봐야 된다 했어요. 온라인 측이 확인을 해봐야 되는 부분이다 얘기를 해가지고 계약 범위 바뀌면"
    },
    {
        "speaker": "SPEAKER_02",
        "start_time": 99.73,
        "end_time": 108.42,
        "text": "아니 근데 이게 왜 저희 쪽에서 확인을 하는 게 아니라 핑거랑 IPK 이런 계약, 그 계약사항이 있는 거 아니에요?"
    },
    {
        "speaker": "SPEAKER_04",
        "start_time": 107.96,
        "end_time": 117.85,
        "text": "네 그 계약사항이 있는데 이게 올라프가 물어보면 어느정도까지 대답을 해주는지가 궁금했었나봐요"
    },
    {
        "speaker": "SPEAKER_02",
        "start_time": 117.38,
        "end_time": 125.48,
        "text": "그 뭐지 블리오 자체도 금융체조는 클라우드에 있는 거잖아요? 왜냐면 금융 데이터가 다 클라우드에 있는 거니까"
    },
    {
        "speaker": "SPEAKER_01",
        "start_time": 124.96,
        "end_time": 125.43,
        "text": "네."
    },
    {
        "speaker": "SPEAKER_02",
        "start_time": 128.13,
        "end_time": 133.5,
        "text": "뭐 얼른 또 물어봐도 뭔가 대장을 하겠지만 전혀 쓸모가 없... 전혀 쓸모없는 대장..."
    },
    {
        "speaker": "SPEAKER_04",
        "start_time": 131.23,
        "end_time": 142.81,
        "text": "전혀 숨었는데도 그거에 대해서 물어보는 것 같더라고요, 그때 보니까. 그래서 제가 일단은 일반적인 체포소로 하고 싶다고 일반적인 그런 금융 같은 수행이 되냐고 해서"
    },
    {
        "speaker": "SPEAKER_04",
        "start_time": 148.62,
        "end_time": 153.27,
        "text": "그래서 이거 같은 경우는 아마 그런 식으로 될 것 같다라고 얘기했는데"
    },
    {
        "speaker": "SPEAKER_04",
        "start_time": 154.07,
        "end_time": 164.46,
        "text": "약간 그때 같이 미팅 했었을 때도 계속 그런 거 막 물어보잖아요. 그냥 간단한 거 물어보면 답변이 나오나요? 계속 그때도 얘기하셨었잖아요."
    },
    {
        "speaker": "SPEAKER_04",
        "start_time": 165.09,
        "end_time": 187.46,
        "text": "그런 거에 대해서 물어보시는 것 같아서 이 2번 같은 경우는 다음 주에 미팅 가서 결과 보여준 다음에 아예 그냥 그때 보여주면서 얘기를 하는 게 어떨 거라고 생각해요. 왜냐하면 2번 같은 경우는 좀 설명을 계속 하는데도 이쪽에 있는 현업에 있는 분들은 이해를 하시는데 노페이 계신 분들은"
    },
    {
        "speaker": "SPEAKER_04",
        "start_time": 188.56,
        "end_time": 192.39,
        "text": "혹시 좀 추가도 안됩니까? 계속 하는거 같애"
    },
    {
        "speaker": "SPEAKER_02",
        "start_time": 191.76,
        "end_time": 241.88,
        "text": "왜냐면 지금 이것도 사실 되게 말이 안되는데 저희가 원래는 업무책봇만 했잖아요 근데 지금 업무책봇 렉을 빌드하고 계신데 업무책봇이라는 게 문서들 다 쪼개서 렉을 만들어서 이렇게 만드는 그런 바람이에요 근데 갑자기 또 이 재무재표도 뭔가 대화하고 싶다라고 해서 저희도 이제 받아야 되는 게 이 재무재표가 결과값이 어떻게 나올지가 왜냐면 이 재무재표 하는 그 db를 그대로 이 렉 쪽이랑 db로 가지고 와서 이렇게 되는 순간 질문이 들어오면 이게 이거인지 이거인지도 한번 판단하는 거를 넣어야 된단 말이에요"
    },
    {
        "speaker": "SPEAKER_01",
        "start_time": 221.14,
        "end_time": 221.4,
        "text": "네."
    },
    {
        "speaker": "SPEAKER_02",
        "start_time": 242.47,
        "end_time": 253.11,
        "text": "이것도 그래서 이거까지 하는... 근데 갑자기 또 해외 주식 담보대축 유니토리 레포트 결과를 또 여기다가 넣으라고 하니 이것도 너무 말이 안 되거든요?"
    },
    {
        "speaker": "SPEAKER_02",
        "start_time": 253.88,
        "end_time": 260.9,
        "text": "그래서 지금 이게 그냥 무슨 책봇 하나인 것 같지만 안무책봇 그리고 재무책봇"
    },
    {
        "speaker": "SPEAKER_02",
        "start_time": 262.4,
        "end_time": 273.51,
        "text": "갑자기 담보대출 모니터링이라고 하지만 결국에는 이거 해외 주식 관련된 거잖아요. 이거랑 이거랑 다를 게 사실 없는 거를"
    },
    {
        "speaker": "SPEAKER_04",
        "start_time": 273.51,
        "end_time": 308.52,
        "text": "그래서 저희가 처음에 생각을 했었던 것은 얘를 눌렀을 때 만약에 이게 카테고리별로 남아지면 눌렀을 때 그거를 이쪽에만 특화된 거를 나오게끔 하는 걸로 얘기를 했었잖아요. 그래서 제가 이거를 얘기를 했어요. 이렇게 해야 된다. 이쪽에서 뭐 첫 번 하나에서 하는 거 말고 얘를 눌렀을 때 얘 특화된 걸로 나오고 얘를 눌렀을 때 얘도 나오고 얘를 눌렀을 때 얘도 나오고 얘를 눌렀을 때 얘도 나오는 거를 보여주는 게 낫지 않냐라고 얘기를 했는데 이 부분은 지금 처음 보내준 거여가지고 이건 어차피 조율을 하면 될 것 같고 하면 될 것 같고"
    },
    {
        "speaker": "SPEAKER_02",
        "start_time": 307.14,
        "end_time": 311.41,
        "text": "근데 사실 그렇다고 하더라도"
    },
    {
        "speaker": "SPEAKER_02",
        "start_time": 312.08,
        "end_time": 339.81,
        "text": "저희는 업로드 챗봇을 했는데, 또 이 챗봇도 만들어야 하고, 이 챗봇도 만들어야 하는 상황인데, 이것까지는 그냥 하는 김에 하자 했는데, 얘는 안되는 이유가 아시다시피 담보대출 모니터링이라는 게, 저희도 이제 그거 쌓아서 이렇게 하는 거잖아요. 그러면 해외 주식에 대한 DV를 또 새로 만들어야 된단 말이에요. 챗봇을 위해서는."
    },
    {
        "speaker": "SPEAKER_00",
        "start_time": 323.02,
        "end_time": 325.48,
        "text": "그냥 하는 김에 하자 했는데 얘는 안되네"
    },
    {
        "speaker": "SPEAKER_02",
        "start_time": 340.55,
        "end_time": 355.47,
        "text": "그래서 이거를 아예 처음에 계약할 때 얘기를 하셨으면 또 그렇게 했을텐데 지금 전혀 뭐랄까 너무 이해 없이 그냥 다 넣어달라고 계속 하시니까 네 그런 느낌일수도 있어요"
    },
    {
        "speaker": "SPEAKER_04",
        "start_time": 353.9,
        "end_time": 374.05,
        "text": "예 그런 느낌일수도 있어요. 그래가지고 제가 일단 얘기를 했던 것 중에 하나는 여기 뒤에 보시면 모니터링 쪽 보시면 관리자 페이지 보시면 이렇게 나왔으면 좋겠다고 하는데 이쪽에 계속 회의록을 집어넣으시길래 회의록을 챕봇을 만들어 달라고 하더라구요. 그래서 이번엔 안된다고 했거든요 제가."
    },
    {
        "speaker": "SPEAKER_04",
        "start_time": 374.93,
        "end_time": 381.05,
        "text": "요거는 안된다. 그리고 그러면서 얘기를 했던게 첫붓이나 이런 추가적인 기능도 있을거면"
    },
    {
        "speaker": "SPEAKER_04",
        "start_time": 381.68,
        "end_time": 389.32,
        "text": "본사업 때 하셔야 된다고 지금은 아마 그냥 간단하게만 이렇게 해서 진행을 하시는 게 낫다라고 얘기를 했거든요"
    },
    {
        "speaker": "SPEAKER_04",
        "start_time": 389.91,
        "end_time": 394.86,
        "text": "시간도 부족하고 그 다음 계약적인 거에서 범위도 넘어간다고 얘기했는데"
    },
    {
        "speaker": "SPEAKER_04",
        "start_time": 395.9,
        "end_time": 402.06,
        "text": "그래서 뭐 알겠다고 얘기는 이거는 뭐 하면서 계속 미팅을 하면서 얘기를 해야 될 것 같고"
    },
    {
        "speaker": "SPEAKER_04",
        "start_time": 403.04,
        "end_time": 406.97,
        "text": "그 부분은 그렇게 하면 될 것 같아요."
    },
    {
        "speaker": "SPEAKER_02",
        "start_time": 404.91,
        "end_time": 416.2,
        "text": "사실 뒤에 더 말씀드릴게 있는데 인터넷 다시 연결하면 안될까봐 네 알겠습니다 그.. 뭐지? 근데 태만님 아시잖아요 저 얼마 받고 하는지"
    },
    {
        "speaker": "SPEAKER_02",
        "start_time": 420.69,
        "end_time": 425.97,
        "text": "아무리 본사원까지 할지 안할지도 모르는 건데"
    },
]

# 화자별 발언 횟수 계산
speaker_counts = Counter(entry['speaker'] for entry in stt_data)

# 발언 횟수 순으로 정렬하여 화자 번호 재매핑
sorted_speakers = [speaker for speaker, _ in speaker_counts.most_common()]
speaker_mapping = {old_speaker: f"SPEAKER_{i:02d}" for i, old_speaker in enumerate(sorted_speakers)}

# 화자 번호 변경
def remap_speakers(data, mapping):
    for entry in data:
        entry['speaker'] = mapping[entry['speaker']]
    return data

updated_stt_data = remap_speakers(stt_data, speaker_mapping)

# 결과 출력
print(json.dumps(updated_stt_data, indent=4, ensure_ascii=False))
