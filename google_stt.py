import os
from dotenv import load_dotenv
from google.cloud import speech
import io
import wave

# Load environment variables
load_dotenv()

GOOGLE_STT_KEY = os.getenv("GOOGLE_API_KEY")


def speech_to_text(
    config: speech.RecognitionConfig,
    audio: speech.RecognitionAudio,
) -> speech.RecognizeResponse:
    client = speech.SpeechClient(client_options={"api_key": GOOGLE_STT_KEY})

    # Synchronous speech recognition request
    response = client.recognize(config=config, audio=audio)

    return response


def print_response(response: speech.RecognizeResponse):
    for result in response.results:
        print_result(result)


def print_result(result: speech.SpeechRecognitionResult):
    best_alternative = result.alternatives[0]
    print("-" * 80)
    print(f"language_code: {result.language_code}")
    print(f"transcript:    {best_alternative.transcript}")
    print(f"confidence:    {best_alternative.confidence:.0%}")



def google_stt_transcribe(client, audio_bytes):
    # client = speech.SpeechClient(client_options={"api_key": GOOGLE_STT_KEY})

    audio = speech.RecognitionAudio(content=audio_bytes)
    config = speech.RecognitionConfig(
        language_code="yue-Hant-HK",  # Cantonese (Traditional, Hong Kong)
        audio_channel_count=1,
        enable_automatic_punctuation=True,  # This can help with sentence structure
        model="default",  # Use the default model, which supports Cantonese
    )
    response = client.recognize(config=config, audio=audio)

    # Extract the transcription from the response
    transcription = ""
    for result in response.results:
        transcription += result.alternatives[0].transcript

    return transcription


def main():
    config = speech.RecognitionConfig(
        language_code="yue-Hant-HK",  # Cantonese (Traditional, Hong Kong)
        audio_channel_count=1,  # Single channel for one speaker
        enable_automatic_punctuation=True,  # This can help with sentence structure
        model="default",  # Use the default model, which supports Cantonese
    )

    audio_file_path = "./test_audio.wav"

    with open(audio_file_path, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)

    response = speech_to_text(config, audio)
    print_response(response)



if __name__ == "__main__":
    main()