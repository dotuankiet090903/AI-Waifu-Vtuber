import websocket
import json
import threading
import soundfile as sf
import sounddevice as sd
import numpy as np
import time

# ------------------------------
# VTube Studio WebSocket
# ------------------------------
VTUBE_WS_URL = "ws://127.0.0.1:8001"  # change if your port is different
PASSWORD = None  # if you set a password in VTube Studio API

def on_open(ws):
    print("[*] Connected to VTube Studio WebSocket")

def on_message(ws, message):
    pass

def on_error(ws, error):
    print("[!] WebSocket Error:", error)

def on_close(ws, close_status_code, close_msg):
    print("[*] WebSocket closed")

ws = websocket.WebSocketApp(
    VTUBE_WS_URL,
    header=[f"Authorization: Bearer {PASSWORD}"] if PASSWORD else None,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

# Run WebSocket in background thread
threading.Thread(target=ws.run_forever, daemon=True).start()
time.sleep(1)  # wait for connection

# ------------------------------
# Send MouthOpen updates
# ------------------------------
def set_mouth_open(value):
    msg = {
        "type": "UpdateModelParameter",
        "parameter": "MouthOpen",
        "value": float(value)  # convert to standard Python float
    }
    ws.send(json.dumps(msg))

# ------------------------------
# Play audio with real-time lip sync
# ------------------------------
def play_audio_with_lip_sync(wav_file):
    data, samplerate = sf.read(wav_file, dtype="float32")
    chunk_size = 1024

    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]

        # Compute simple amplitude (volume)
        amplitude = np.abs(chunk).mean()
        mouth_value = min(max(amplitude * 5, 0.0), 1.0)  # scale 0-1
        set_mouth_open(mouth_value)

        # Play the chunk
        sd.play(chunk, samplerate)
        sd.wait()

    # Ensure mouth closes at the end
    set_mouth_open(0.0)

# ------------------------------
# Main Test
# ------------------------------
if __name__ == "__main__":
    print("Starting test... Make sure VTube Studio is running and API is ON.")
    test_wav = "test.wav"  # replace with your TTS audio
    play_audio_with_lip_sync(test_wav)
    print("Test finished.")
