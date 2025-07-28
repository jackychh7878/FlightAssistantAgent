import os
from dotenv import load_dotenv
from google.cloud import texttospeech


# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def google_tts_response(client, text, language_code="yue-HK"):
    # Instantiates a client
    # client = texttospeech.TextToSpeechClient(client_options={"api_key": GOOGLE_API_KEY})

    # Preprocess the text to handle LaTeX expressions
    # processed_text = preprocess_text(text)

    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Build the voice request, select the language code and the ssml voice gender
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code, ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Perform the text-to-speech request
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # Return the audio content as bytes
    return response.audio_content


def main():
    with open("output.mp3", "wb") as out:
        # Write the response to the output file.
        request_audio = google_tts_response(texttospeech.TextToSpeechClient(client_options={"api_key": GOOGLE_API_KEY}),
                                            text="你計算的答案是 $7 + 5 = 11$ 嗎？這裡有一個提示，你再檢查一下 7 加 5 的總和是什麼。你可以試試用手指來數一下，看看能不能得到不同的結果？")

        out.write(request_audio)
        print('Audio content written to file "output.mp3"')

if __name__ == "__main__":
    main()