import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
from io import BytesIO

# Load environment variables
load_dotenv()


def azure_tts_response(text):
    speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('AZURE_TTS_KEY'), region=os.environ.get('AZURE_TTS_REGION'))
    # Auto play testing
    # audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

    # The neural multilingual voice can speak different languages based on the input text.
    speech_config.speech_synthesis_voice_name='en-US-AvaMultilingualNeural'

    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)

    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()

    return speech_synthesis_result.audio_data


# print(azure_tts_response(text="testing"))