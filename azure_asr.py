import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
from pydub import AudioSegment
import tempfile
import wave
import io

# Load environment variables
load_dotenv()



def recognize_from_microphone():
    # This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
    speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), region=os.environ.get('SPEECH_REGION'))
    # speech_config.speech_recognition_language = "ja-JP"
    # speech_config.speech_recognition_language="zh-HK"

    auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(languages=["ja-JP", "zh-HK", "zh-CN", "ko-KR"])


    # sample_audio = "./sample_audio/pronunciation_ja.wav"
    # sample_audio = "./sample_audio/pronunciation_yue.wav"
    # sample_audio = "./sample_audio/pronunciation_zh_一起喝杯咖啡？.wav"
    sample_audio = "./sample_audio/pronunciation_ko_저랑_커피_한_잔_하실래요_.wav"
    audio_config = speechsdk.audio.AudioConfig(filename=sample_audio)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config, auto_detect_source_language_config=auto_detect_source_language_config)

    print("Recognizing audio...")
    # speech_recognition_result = speech_recognizer.recognize_once_async().get()
    speech_recognition_result = speech_recognizer.recognize_once()

    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print("Recognized: {}".format(speech_recognition_result.text))
    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_recognition_result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
            print("Did you set the speech resource key and region values?")


def azure_stt_transcribe(audio_bytes):
    # This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
    speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), region=os.environ.get('SPEECH_REGION'))
    # speech_config.speech_recognition_language = "ja-JP"
    # speech_config.speech_recognition_language="zh-HK"

    auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(languages=["ja-JP", "zh-HK", "zh-CN", "ko-KR"])

    # Create a temporary WAV file from the audio_bytes
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav_file:
        temp_wav_path = temp_wav_file.name

        # If audio_bytes is already in WAV format, write directly
        try:
            with wave.open(io.BytesIO(audio_bytes)) as wave_check:
                # If we can open it as a WAV file, it's already in WAV format
                temp_wav_file.write(audio_bytes)
        except:
            # If it's not in WAV format, you'll need conversion logic here
            # This is a simplified example - you may need a library like pydub for proper conversion
            raise ValueError("Input audio_bytes is not in WAV format. Conversion is required.")

    try:
        # Create AudioConfig using the temporary file
        # audio_wav = "./sample_audio/pronunciation_yue.wav"
        audio_config = speechsdk.audio.AudioConfig(filename=temp_wav_path)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config,
                                                       audio_config=audio_config,
                                                       auto_detect_source_language_config=auto_detect_source_language_config)

        speech_recognition_result = speech_recognizer.recognize_once()


        if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return speech_recognition_result.text
        else:
            return f"Recognition failed: {speech_recognition_result.reason}"
    finally:
        # Delay file deletion to prevent access issues
        # Use a separate try/except to avoid suppressing recognition errors
        try:
            # Add a small delay to ensure file is released (optional)
            import time
            time.sleep(0.1)

            if os.path.exists(temp_wav_path):
                os.unlink(temp_wav_path)
        except Exception as e:
            print(f"Warning: Could not delete temporary file {temp_wav_path}: {e}")


def azure_stt_transcribe_from_mic():
    # This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
    speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('AZURE_ASR_KEY'), region=os.environ.get('AZURE_ASR_REGION'))
    # speech_config.speech_recognition_language = "ja-JP"
    # speech_config.speech_recognition_language="zh-HK"

    #https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=stt
    support_language_list = ["zh-HK", "zh-CN", #Chinese
                             "ja-JP", #Japanese
                             "ko-KR", #Korean
                             # "hi-IN", #Hindi
                             # "fil-PH", #Philipp
                             # "th-TH", #Thai
                             # "id-ID", #Indonesian,
                             # "ru-RU", #Russian
                             # "de-DE", #German
                             # "fr-CA", "fr-FR", #French
                             # "it-CH", "it-IT", #Italian
                             # "es-ES" #Spanish
                             ]
    auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(languages=support_language_list)
    # Create AudioConfig using the temporary file
    # audio_wav = "./sample_audio/pronunciation_yue.wav"
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config,
                                                   audio_config=audio_config,
                                                   auto_detect_source_language_config=auto_detect_source_language_config)

    speech_recognition_result = speech_recognizer.recognize_once_async().get()

    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return speech_recognition_result.text
    else:
        return f"Recognition failed: {speech_recognition_result.reason}"



if __name__ == "__main__":
    recognize_from_microphone()