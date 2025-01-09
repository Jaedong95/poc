# Copyright 2023-2024 Deepgram SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

import json
import os
from dotenv import load_dotenv
import logging
from deepgram.utils import verboselogs
from datetime import datetime
import httpx

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    PrerecordedOptions,
    FileSource,
)

load_dotenv()

AUDIO_FILE = "./meeting_records/wav/전략기획사업단_01.wav"
save_file_name = "deepgram_" + AUDIO_FILE.split('/')[-1].split('.')[0] + '.json'

def main():
    # STEP 1 Create a Deepgram client using the API key in the environment variables
    config: DeepgramClientOptions = DeepgramClientOptions(
        verbose=verboselogs.SPAM,
    )
    deepgram: DeepgramClient = DeepgramClient("8689b7cc7255124e64e717d93b6a2cb4e6702b36", config)

    # STEP 2 Call the transcribe_file method on the rest class
    with open(AUDIO_FILE, "rb") as file:
        buffer_data = file.read()

    payload: FileSource = {
        "buffer": buffer_data,
    }

    options: PrerecordedOptions = PrerecordedOptions(
        model="nova-2",
        smart_format=True,
        utterances=True,
        language='ko',
        punctuate=False,
        diarize=True,
    )
    before = datetime.now()
    response = deepgram.listen.rest.v("1").transcribe_file(
        payload, options, timeout=httpx.Timeout(300.0, connect=10.0)
    )
    after = datetime.now()
    json_result = response.to_json(indent=4, ensure_ascii=False)
    parsed_result = response.to_dict()

    # Utterances 출력
    if "utterances" in parsed_result["results"]:
        utterances = parsed_result["results"]["utterances"]
        for idx, utterance in enumerate(utterances, start=1):
            print(f"Utterance {idx}:")
            print(f" - Start Time: {utterance['start']}")
            print(f" - End Time: {utterance['end']}")
            print(f" - Transcript: {utterance['transcript']}")
            print("")
    else:
        print("No utterances found in the response.")

    # 필요한 정보만 저장하도록 세그먼트 단위를 정리
    formatted_segments = []
    for segment in parsed_result["results"]["utterances"]:
        formatted_segments.append({
            "start": segment["start"],
            "end": segment["end"],
            "transcript": segment["transcript"],
            "confidence": segment["confidence"]
        })

    with open(save_file_name, "w", encoding="utf-8") as f:
        json.dump(formatted_segments, f, ensure_ascii=False, indent=4)

    with open('./deepgram_records.json', "w", encoding="utf-8") as f:
        f.write(json_result)
    print("")
    difference = after - before
    print(f"time: {difference.seconds}")

if __name__ == "__main__":
    main()