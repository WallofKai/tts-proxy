from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    text = data.get('text')
    voice = data.get('voice', 'en-US-Wavenet-D')
    api_key = os.getenv('GOOGLE_API_KEY')

    if not text or not api_key:
        return jsonify({"error": "Missing text or API key"}), 400

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
        return jsonify({"error": "Google TTS failed"}), 500

    audio_content = res.json().get("audioContent")
    return jsonify({"audio_url": f"data:audio/mp3;base64,{audio_content}"})
