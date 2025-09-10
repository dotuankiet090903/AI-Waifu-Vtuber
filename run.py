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
from utils.TTS import *
from utils.subtitle import *
from utils.promptMaker import *
from utils.twitch_config import *
import google.generativeai as genai

# to help the CLI write unicode characters to the terminal
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)

# use your own API Key, you can get it from https://openai.com/. I place my API Key in a separate file called config.py
openai.api_key = GPT_api_key

# Configure Gemini 
genai.configure(api_key=Gemini_api_key)


conversation = []
# Create a dictionary to hold the message data
history = {"history": conversation}

mode = 0
total_characters = 0
chat = ""
chat_now = ""
chat_prev = ""
is_Speaking = False
owner_name = "Kiet"
blacklist = ["Nightbot", "streamelements"]

# function to get the user's input audio
def record_audio():
    MIC_INDEX = 1  # your mic index
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    WAVE_OUTPUT_FILENAME = "input.wav"
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    input_device_index=MIC_INDEX)
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
    # transcribe_audio("input.wav")
    transcribe_audio_Gemini("input.wav")

# function to transcribe the user's audio OpenAI
# def transcribe_audio(file):
#     global chat_now
#     try:
#         audio_file= open(file, "rb")
#         # Translating the audio to English
#         # transcript = openai.Audio.translate("whisper-1", audio_file)
#         # Transcribe the audio to detected language
#         transcript = openai.Audio.transcribe("whisper-1", audio_file)
#         chat_now = transcript.text
#         print ("Question: " + chat_now)
#     except Exception as e:
#         print("Error transcribing audio: {0}".format(e))
#         return

#     result = owner_name + " said " + chat_now
#     conversation.append({'role': 'user', 'content': result})
#     openai_answer()

# function to get an answer from OpenAI
# def openai_answer():
#     global total_characters, conversation

#     total_characters = sum(len(d['content']) for d in conversation)

#     while total_characters > 4000:
#         try:
#             # print(total_characters)
#             # print(len(conversation))
#             conversation.pop(2)
#             total_characters = sum(len(d['content']) for d in conversation)
#         except Exception as e:
#             print("Error removing old messages: {0}".format(e))

#     with open("conversation.json", "w", encoding="utf-8") as f:
#         # Write the message data to the file in JSON format
#         json.dump(history, f, indent=4)

#     prompt = getPrompt()

#     response = openai.ChatCompletion.create(
#         model="gpt-3.5-turbo",
#         messages=prompt,
#         max_tokens=128,
#         temperature=1,
#         top_p=0.9
#     )
#     message = response['choices'][0]['message']['content']
#     conversation.append({'role': 'assistant', 'content': message})

#     translate_text(message)

# function to transcribe the user's audio Gemini
import speech_recognition as sr
import traceback

def transcribe_audio_Gemini(file):
    global chat_now
    r = sr.Recognizer()
    with sr.AudioFile(file) as source:
        audio = r.record(source)
    try:
        chat_now = r.recognize_google(audio, language="en-EN")  # choose language
        print("Question: " + chat_now)
    except Exception as e:
        print("Error transcribing audio:", str(e))
        traceback.print_exc()   # <-- shows full error in terminal
        return
    
    result = owner_name + " said " + chat_now
    conversation.append({'role': 'user', 'content': result})
    gemini_answer()


# function to get an answer from Gemini
def gemini_answer():
    global total_characters, conversation

    # Calculate total character count in conversation
    total_characters = sum(len(d['content']) for d in conversation)

    # Trim conversation if it gets too long
    while total_characters > 4000:
        try:
            conversation.pop(2)  # remove older message but keep system + recent
            total_characters = sum(len(d['content']) for d in conversation)
        except Exception as e:
            print("Error removing old messages: {0}".format(e))

    # Save conversation history to JSON
    with open("conversation.json", "w", encoding="utf-8") as f:
        json.dump(conversation, f, indent=4, ensure_ascii=False)

    # Build prompt (assuming your getPrompt() formats it properly)
    prompt = getPrompt()
    ("DEBUG PROMPT:", prompt) 
    
    
    # Create Gemini model
    # model = genai.GenerativeModel("models/gemini-1.5-flash", system_instruction="You are a helpful assistant. Always answer in English.")
    model = genai.GenerativeModel("models/gemini-1.5-flash", system_instruction="You are a helpful assistant. Always reply with text only, no audio.")


    # Send the request
    response = model.generate_content(prompt)

    # Extract message text
    if response and response.candidates:
        message = response.candidates[0].content.parts[0].text
    else:
        message = "⚠️ No response from Gemini."

    # Append Gemini’s response to conversation
    conversation.append({'role': 'model', 'content': message})

    # Translate message (if your translate_text() exists)
    translate_text(message)


# function to capture livechat from youtube
def yt_livechat(video_id):
        global chat

        live = pytchat.create(video_id=video_id)
        while live.is_alive():
        # while True:
            try:
                for c in live.get().sync_items():
                    # Ignore chat from the streamer and Nightbot, change this if you want to include the streamer's chat
                    if c.author.name in blacklist:
                        continue
                    # if not c.message.startswith("!") and c.message.startswith('#'):
                    if not c.message.startswith("!"):
                        # Remove emojis from the chat
                        chat_raw = re.sub(r':[^\s]+:', '', c.message)
                        chat_raw = chat_raw.replace('#', '')
                        # chat_author makes the chat look like this: "Nightbot: Hello". So the assistant can respond to the user's name
                        chat = c.author.name + ' berkata ' + chat_raw
                        print(chat)
                        
                    time.sleep(1)
            except Exception as e:
                print("Error receiving chat: {0}".format(e))

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

            elif not user in resp:
                resp = demojize(resp)
                match = re.match(regex, resp)

                username = match.group(1)
                message = match.group(2)

                if username in blacklist:
                    continue
                
                chat = username + ' said ' + message
                print(chat)

        except Exception as e:
            print("Error receiving chat: {0}".format(e))

import pyaudio
import numpy as np
import soundfile as sf

def play_tts_dual(audio_array, sample_rate=44100):
    audio_int16 = (audio_array * 32767).astype(np.int16)
    audio_bytes = audio_int16.tobytes()
    
    p = pyaudio.PyAudio()
    
    # Replace with your device indices
    cable1_index = 5  # CABLE Input 1 (VB-Audio) → VTube Studio
    cable2_index = 7  # CABLE Input 2 (VB-Audio) → Speakers
    
    # Open stream to Cable1
    stream_cable1 = p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=sample_rate,
                            output=True,
                            output_device_index=cable1_index)
    
    # Open stream to Cable2
    stream_cable2 = p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=sample_rate,
                            output=True,
                            output_device_index=cable2_index)
    
    # Write audio to both streams
    stream_cable1.write(audio_bytes)
    stream_cable2.write(audio_bytes)
    
    stream_cable1.stop_stream()
    stream_cable1.close()
    
    stream_cable2.stop_stream()
    stream_cable2.close()
    
    p.terminate()

# translating is optional
def translate_text(text):
    global is_Speaking
    # subtitle will act as subtitle for the viewer
    # subtitle = translate_google(text, "ID")

    # tts will be the string to be converted to audio
    detect = detect_google(text)
    tts = translate_google(text, f"{detect}", "JA")
    # tts = translate_deeplx(text, f"{detect}", "JA")
    tts_en = translate_google(text, f"{detect}", "EN")
    # tts = text
    try:
        # print("ID Answer: " + subtitle)
        print("JP Answer: " + tts)
        print("EN Answer: " + tts_en)
        # print("EN Answer: " + tts)
    except Exception as e:
        print("Error printing text: {0}".format(e))
        return

    # Choose between the available TTS engines
    # Japanese TTS
    voicevox_tts(tts)

    # Silero TTS, Silero TTS can generate English, Russian, French, Hindi, Spanish, German, etc. Uncomment the line below. Make sure the input is in that language
    # silero_tts(tts_en, "en", "v3_en", "en_21")

    # Generate Subtitle
    generate_subtitle(chat_now, text)

    time.sleep(1)

    # is_Speaking is used to prevent the assistant speaking more than one audio at a time
    # is_Speaking = True
    # winsound.PlaySound("test.wav", winsound.SND_FILENAME)
    # is_Speaking = False

    audio_array, sample_rate = sf.read("test.wav", dtype='float32')
    play_tts_dual(audio_array, sample_rate)

    # Clear the text files after the assistant has finished speaking
    time.sleep(1)
    with open ("output.txt", "w") as f:
        f.truncate(0)
    with open ("chat.txt", "w") as f:
        f.truncate(0)
    
    speech_text(tts, tts_en)
    # speech_text(tts)

def speech_text(tts, tts_en):
    global is_Speaking
    katakana_text = katakana_converter(tts_en)

# def speech_text(tts):
#     global is_Speaking
#     katakana_text = katakana_converter(tts)

def preparation():
    global conversation, chat_now, chat, chat_prev
    while True:
        # If the assistant is not speaking, and the chat is not empty, and the chat is not the same as the previous chat
        # then the assistant will answer the chat
        chat_now = chat
        if is_Speaking == False and chat_now != chat_prev:
            # Saving chat history
            conversation.append({'role': 'user', 'content': chat_now})
            chat_prev = chat_now
            gemini_answer()
        time.sleep(1)

if __name__ == "__main__":
    try:
        # You can change the mode to 1 if you want to record audio from your microphone
        # or change the mode to 2 if you want to capture livechat from youtube
        mode = input("Mode (1-Mic, 2-Youtube Live, 3-Twitch Live): ")

        if mode == "1":
            print("Press and Hold Right Shift to record audio")
            while True:
                if keyboard.is_pressed('RIGHT_SHIFT'):
                    record_audio()
            
        elif mode == "2":
            live_id = input("Livestream ID: ")
            # Threading is used to capture livechat and answer the chat at the same time
            t = threading.Thread(target=preparation)
            t.start()
            yt_livechat(live_id)

        elif mode == "3":
            # Threading is used to capture livechat and answer the chat at the same time
            print("To use this mode, make sure to change utils/twitch_config.py to your own config")
            t = threading.Thread(target=preparation)
            t.start()
            twitch_livechat()
    except KeyboardInterrupt:
        t.join()
        print("Stopped")

