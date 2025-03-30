from flask import Flask, request, jsonify, send_from_directory
import requests
import os
import base64
import textwrap
from datetime import datetime

app = Flask(__name__)
STATIC_DIR = os.path.join(os.getcwd(), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

def split_text(text, max_chars=900):
    return textwrap.wrap(text, max_chars, break_long_words=False, break_on_hyphens=False)

def synthesize_chunk(text, voice, api_key):
    tts_url = "https://texttospeech.googleapis.com/v1/text:synthesize"
    headers = {"X-Goog-Api-Key": api_key}
    payload = {
        "input": {"text": text},
        "voice": {"languageCode": "en-US", "name": voice},
        "audioConfig": {"audioEncoding": "MP3"}
    }

    res = requests.post(tts_url, headers=headers, json=payload)
    if res.status_code != 200:
        raise Exception(f"TTS API error: {res.text}")
    return base64.b64decode(res.json()["audioContent"])

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
        audio_segments = [synthesize_chunk(chunk, voice, api_key) for chunk in chunks]
        full_audio = b"".join(audio_segments)

        # Save to static folder
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"audio_{timestamp}.mp3"
        file_path = os.path.join(STATIC_DIR, filename)

        with open(file_path, "wb") as f:
            f.write(full_audio)

        file_url = f"https://tts-proxy.onrender.com/static/{filename}"
        return jsonify({"audio_url": file_url})

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500

# Optional direct access to static files (just in case)
@app.route('/static/<filename>')
def static_file(filename):
    return send_from_directory(STATIC_DIR, filename)
