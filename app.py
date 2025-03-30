from flask import Flask, request, jsonify
import requests
import os
import base64
import textwrap

app = Flask(__name__)

def split_text(text, max_chars=900):
    # Break at sentence boundaries (preferably) or spaces
    wrapped = textwrap.wrap(text, max_chars, break_long_words=False, break_on_hyphens=False)
    return wrapped

def synthesize_chunk(text, voice, api_key):
    tts_url = "https://texttospeech.googleapis.com/v1/text:synthesize"
    headers = {"X-Goog-Api-Key": api_key}
    payload = {
        "input": {"text": text},
        "voice": {
            "languageCode": "en-US",
            "name": voice
        },
        "audioConfig": {
            "audioEncoding": "MP3"
        }
    }

    res = requests.post(tts_url, headers=headers, json=payload)
    if res.status_code != 200:
        raise Exception(f"TTS API error: {res.text}")
    return res.json()["audioContent"]

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    text = data.get("text")
    voice = data.get("voice", "en-US-Wavenet-D")
    api_key = os.getenv("GOOGLE_API_KEY")

    if not text or not api_key:
        return jsonify({"error": "Missing text or API key"}), 400

    try:
        chunks = split_text(text)
        audio_segments = []

        for chunk in chunks:
            audio_b64 = synthesize_chunk(chunk, voice, api_key)
            audio_segments.append(base64.b64decode(audio_b64))

        # Concatenate all decoded audio bytes
        full_audio = b''.join(audio_segments)
        audio_b64_combined = base64.b64encode(full_audio).decode("utf-8")
        audio_data_url = f"data:audio/mp3;base64,{audio_b64_combined}"

        return jsonify({"audio_url": audio_data_url})
    except Exception as e:
    print("Error during synthesis:", str(e))
    return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app
