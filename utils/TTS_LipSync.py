# vtuber_lipsync_test.py
import os
import requests
import urllib.parse
import sounddevice as sd
import soundfile as sf
import numpy as np
import websocket
import json
import threading
import time
from utils.katakana import katakana_converter

# ------------------------------
# VTube Studio WebSocket Setup
# ------------------------------
VTUBE_WS_URL = "ws://127.0.0.1:8001"  # Change if your port is different
PASSWORD = None  # Add password if used

ws = None

def start_vtube_ws():
    global ws
    ws = websocket.WebSocketApp(
        VTUBE_WS_URL,
        on_open=lambda w: print("[*] Connected to VTube Studio WebSocket"),
        on_message=lambda w, msg: None,
        on_error=lambda w, err: print("[!] VTube Studio WebSocket Error:", err),
        on_close=lambda w, code, msg: print("[*] VTube Studio WS closed")
    )
    threading.Thread(target=ws.run_forever, daemon=True).start()
    time.sleep(1)  # wait for connection

def set_mouth_open(value):
    """Send MouthOpen parameter to VTube Studio (0.0 closed, 1.0 open)"""
    if ws:
        msg = {
            "type": "UpdateModelParameter",
            "parameter": "MouthOpen",  # input param mapped to ParamMouthOpenY
            "value": float(value)
        }
        ws.send(json.dumps(msg))
        print(f"[DEBUG] MouthOpen value sent: {value:.2f}")

# ------------------------------
# Voicevox TTS
# ------------------------------
def voicevox_tts(tts_text, filename="test.wav", speaker=8):
    voicevox_url = "http://localhost:50021"
    katakana_text = katakana_converter(tts_text)

    # 1. Generate audio query
    params_encoded = urllib.parse.urlencode({'text': katakana_text, 'speaker': speaker})
    query = requests.post(f'{voicevox_url}/audio_query?{params_encoded}').json()

    # 2. Synthesize audio
    params_encoded2 = urllib.parse.urlencode({'speaker': speaker, 'enable_interrogative_upspeak': True})
    response = requests.post(f'{voicevox_url}/synthesis?{params_encoded2}', json=query)

    # 3. Save WAV file
    with open(filename, "wb") as f:
        f.write(response.content)

    return filename

# ------------------------------
# Play WAV with real-time lip sync
# ------------------------------
def play_audio_with_lip_sync(wav_file):
    data, samplerate = sf.read(wav_file, dtype="float32")
    chunk_size = 512  # smaller chunks = smoother lip movement

    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]

        # Calculate amplitude and scale to 0-1
        amplitude = np.abs(chunk).mean()
        mouth_value = min(max(amplitude * 15, 0.0), 1.0)  # stronger multiplier for noticeable lips

        # Update lips in VTube Studio
        set_mouth_open(mouth_value)

        # Play audio chunk
        sd.play(chunk, samplerate)
        sd.wait()

    # Close mouth at the end
    set_mouth_open(0.0)

# ------------------------------
# Combined function
# ------------------------------
def speak_text(text):
    wav_file = voicevox_tts(text)
    play_audio_with_lip_sync(wav_file)

# ------------------------------
# Main
# ------------------------------
if __name__ == "__main__":
    start_vtube_ws()
    time.sleep(1)  # allow WebSocket to connect
    speak_text("Hello! I am your AI VTuber speaking with lip sync!")
