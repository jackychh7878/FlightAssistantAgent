import os
from dotenv import load_dotenv
import requests
import base64

load_dotenv()

FANOLAB_API_KEY = os.getenv("FANOLAB_API_KEY")

def fanolab_stt_transcribe(audio_bytes):
    url = "https://portal-demo.fano.ai/speech/recognize"

    # Convert audio bytes to Base64
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    # Prepare payload
    payload = {
        "config": {
            "languageCode": "yue",
            "maxAlternatives": 2,
            "enableSeparateRecognitionPerChannel": False,
            "enableAutomaticPunctuation": True
        },
        "enableWordTimeOffsets": True,
        "diarizationConfig": {
            "disableSpeakerDiarization": False
        },
        "audio": {
            "content": audio_base64
        }
    }


    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {FANOLAB_API_KEY}"}

    # Make the POST request
    response = requests.post(url, json=payload, headers=headers)
    response_data = response.json()

    print(response_data)

    # Extract and join all transcripts
    transcripts = []
    for result in response_data.get("results", []):
        for alternative in result.get("alternatives", []):
            if "transcript" in alternative:
                transcripts.append(alternative["transcript"])

    # return "".join(transcripts)
    print(transcripts)
    return transcripts[0]

def fanolab_tts_response(text, language_code="yue", encoding="LINEAR16", sample_rate_hertz="8000"):
    url = "https://portal-demo.fano.ai/speech/synthesize-speech"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {FANOLAB_API_KEY}"}

    payload = {
        "input": {"text": text},
        "voice": {"languageCode": language_code},
        "audioConfig": {
            "encoding": encoding,
            "sampleRateHertz": sample_rate_hertz
        }
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        audio_content = response.json().get("audioContent")
        if audio_content:
            return base64.b64decode(audio_content)

    raise Exception(f"Error: {response.status_code}, {response.text}")
