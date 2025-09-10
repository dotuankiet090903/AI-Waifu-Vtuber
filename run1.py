import openai
import winsound
import sys
import pytchat
import time
import re
import pyaudio
import keyboard
import wave
import threading
import json
import socket
from emoji import demojize
from config import *
from utils.katakana import *
from utils.translate import *
from utils.TTS_LipSync import *
from utils.subtitle import *
from utils.promptMaker import *
from utils.twitch_config import *
import google.generativeai as genai
import websocket
import traceback
import speech_recognition as sr

# ------------------------------
# VTube Studio WebSocket Setup
# ------------------------------
start_vtube_ws()

def send_message(ws, message):
    ws.send(json.dumps(message))

def trigger_expression(expression_name):
    global ws
    if ws:
        msg = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": str(time.time()),
            "messageType": "SetExpression",
            "data": {"expressionName": expression_name}
        }
        send_message(ws, msg)

def on_open(_ws):
    print("[*] Connected to VTube Studio WebSocket")

def on_message(_ws, message):
    pass

def on_error(_ws, error):
    print("[!] VTube Studio WebSocket Error:", error)

def on_close(_ws):
    print("[*] VTube Studio WebSocket closed")

def start_vtube_ws():
    global ws
    ws = websocket.WebSocketApp(
        VTUBE_WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws_thread = threading.Thread(target=ws.run_forever)
    ws_thread.daemon = True
    ws_thread.start()
    time.sleep(1)

# ------------------------------
# Globals
# ------------------------------
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)
openai.api_key = GPT_api_key
genai.configure(api_key=Gemini_api_key)

conversation = []
history = {"history": conversation}
mode = 0
total_characters = 0
chat = ""
chat_now = ""
chat_prev = ""
is_Speaking = False
owner_name = "Kiet"
blacklist = ["Nightbot", "streamelements"]

# ------------------------------
# Audio Recording
# ------------------------------
def record_audio():
    MIC_INDEX = 1
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    WAVE_OUTPUT_FILENAME = "input.wav"
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                    frames_per_buffer=CHUNK, input_device_index=MIC_INDEX)
    frames = []
    print("Recording...")
    while keyboard.is_pressed('RIGHT_SHIFT'):
        data = stream.read(CHUNK)
        frames.append(data)
    print("Stopped recording.")
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    transcribe_audio_Gemini(WAVE_OUTPUT_FILENAME)

# ------------------------------
# Gemini Transcription & Response
# ------------------------------
def transcribe_audio_Gemini(file):
    global chat_now
    r = sr.Recognizer()
    with sr.AudioFile(file) as source:
        audio = r.record(source)
    try:
        chat_now = r.recognize_google(audio, language="en-EN")
        print("Question: " + chat_now)
    except Exception as e:
        print("Error transcribing audio:", str(e))
        traceback.print_exc()
        return
    
    result = owner_name + " said " + chat_now
    conversation.append({'role': 'user', 'content': result})
    gemini_answer()

def gemini_answer():
    global total_characters, conversation

    total_characters = sum(len(d['content']) for d in conversation)
    while total_characters > 4000:
        conversation.pop(2)
        total_characters = sum(len(d['content']) for d in conversation)

    with open("conversation.json", "w", encoding="utf-8") as f:
        json.dump(conversation, f, indent=4, ensure_ascii=False)

    prompt = getPrompt()
    model = genai.GenerativeModel("models/gemini-1.5-flash",
                                  system_instruction="You are a helpful assistant. Reply with text only.")
    response = model.generate_content(prompt)

    if response and response.candidates:
        message = response.candidates[0].content.parts[0].text
    else:
        message = "⚠️ No response from Gemini."

    conversation.append({'role': 'model', 'content': message})
    # ------------------------------
    # Trigger Emotion & Talking Expression
    # ------------------------------
    
    start_speaking_expression(message)
    translate_text(message)

def start_speaking_expression(message):
    global is_Speaking
    is_Speaking = True

    # Trigger emotional expression before speaking
    if any(word in message.lower() for word in ["happy", "good", "love", "fun"]):
        trigger_expression("Smile")
    elif any(word in message.lower() for word in ["sad", "angry", "hate", "upset"]):
        trigger_expression("Angry")
    else:
        trigger_expression("Neutral")

    # Trigger talking expression while TTS plays
    trigger_expression("Talking")
    time.sleep(0.1)  # short delay to ensure expression change

    is_Speaking = False
    trigger_expression("Neutral")  # revert after speaking

# ------------------------------
# Translate & TTS
# ------------------------------
import wave
import pyaudio
import time

def play_audio_with_talking(wav_file):
    wf = wave.open(wav_file, 'rb')
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    chunk_size = 1024
    trigger_expression("Talking")  # start talking

    data = wf.readframes(chunk_size)
    while data:
        stream.write(data)
        data = wf.readframes(chunk_size)

    stream.stop_stream()
    stream.close()
    p.terminate()

    trigger_expression("Neutral")  # revert expression

def translate_text(text):
    detect = detect_google(text)
    tts = translate_google(text, f"{detect}", "JA")
    tts_en = translate_google(text, f"{detect}", "EN")

    print("JP Answer: " + tts)
    print("EN Answer: " + tts_en)

    # Generate WAV file first
    voicevox_tts(tts)  # ensure your TTS can save to WAV

    # Play audio while triggering talking expression
    play_audio_with_talking("test.wav")

    # Generate subtitle
    generate_subtitle(chat_now, text)

# ------------------------------
# LiveChat Functions
# ------------------------------
def yt_livechat(video_id):
    global chat
    live = pytchat.create(video_id=video_id)
    while live.is_alive():
        try:
            for c in live.get().sync_items():
                if c.author.name in blacklist:
                    continue
                if not c.message.startswith("!"):
                    chat_raw = re.sub(r':[^\s]+:', '', c.message)
                    chat_raw = chat_raw.replace('#', '')
                    chat = c.author.name + ' said ' + chat_raw
                    print(chat)
                time.sleep(1)
        except Exception as e:
            print("Error receiving chat:", e)

def twitch_livechat():
    global chat
    sock = socket.socket()
    sock.connect((server, port))
    sock.send(f"PASS {token}\n".encode('utf-8'))
    sock.send(f"NICK {nickname}\n".encode('utf-8'))
    sock.send(f"JOIN {channel}\n".encode('utf-8'))
    regex = r":(\w+)!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :(.+)"
    while True:
        try:
            resp = sock.recv(2048).decode('utf-8')
            if resp.startswith('PING'):
                sock.send("PONG\n".encode('utf-8'))
            else:
                resp = demojize(resp)
                match = re.match(regex, resp)
                username = match.group(1)
                message = match.group(2)
                if username in blacklist:
                    continue
                chat = username + ' said ' + message
                print(chat)
        except Exception as e:
            print("Error receiving chat:", e)

# ------------------------------
# Preparation Loop
# ------------------------------
def preparation():
    global conversation, chat_now, chat, chat_prev
    while True:
        chat_now = chat
        if not is_Speaking and chat_now != chat_prev:
            conversation.append({'role': 'user', 'content': chat_now})
            chat_prev = chat_now
            gemini_answer()
        time.sleep(1)

# ------------------------------
# Main
# ------------------------------
if __name__ == "__main__":
    start_vtube_ws()

    try:
        mode = input("Mode (1-Mic, 2-Youtube Live, 3-Twitch Live): ")

        if mode == "1":
            print("Press and Hold Right Shift to record audio")
            while True:
                if keyboard.is_pressed('RIGHT_SHIFT'):
                    record_audio()

        elif mode == "2":
            live_id = input("Livestream ID: ")
            t = threading.Thread(target=preparation)
            t.start()
            yt_livechat(live_id)

        elif mode == "3":
            print("Make sure twitch_config.py is set")
            t = threading.Thread(target=preparation)
            t.start()
            twitch_livechat()

    except KeyboardInterrupt:
        print("Stopped")
