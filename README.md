# AI-Waifu-Vtuber
Using a variety of technologies, including VoiceVox Engine, DeepL, Seliro TTS, and VtubeStudio, this project draws inspiration from Ardha. It is designed to adjust to data structures and prompt creators that match the Gemini model rather than the OpenAI model in the original code to create an AI waifu virtual.

## Technologies Used

 - [VoiceVox Docker](https://hub.docker.com/r/voicevox/voicevox_engine) or [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/SociallyIneptWeeb/LanguageLeapAI/blob/main/src/run_voicevox_colab.ipynb)
 - [DeepL](https://www.deepl.com/fr/account/summary)
 - [Deeplx](https://github.com/OwO-Network/DeepLX)
 - [Whisper OpenAI](https://platform.openai.com/account/api-keys)
 - [Seliro TTS](https://github.com/snakers4/silero-models#text-to-speech)
 - [VB-Cable](https://vb-audio.com/Cable/)
 - VtubeStudio

## Installation

1. Install the dependencies

```
pip install -r requirements.txt
```

2. Create a config.py inside the same folder with run.py and store your Gemini API key like this:

```
Gemini_api_key = 'yourapikey'
```

3. Change the owner name

```
owner_name = "Kiet"
```

if you want to use it for livestream, create a list of users that you want to blacklist on `run.py`

```
blacklist = ["Nightbot", "streamelements"]
```

4. Change the lore or identity of your assistant. Change the txt file at `characterConfig\Pina\identity.txt`

5. If you want to stream on Twitch you need to change the config file at `utils/twitch_config.py`. Get your token from [Here](https://twitchapps.com/tmi/). Your token should look something like oauth:43rip6j6fgio8n5xly1oum1lph8ikl1 (fake for this tutorial). After you change the config file, you can start the program using Mode - 3
```
server = 'irc.chat.twitch.tv'
port = 6667
nickname = 'testing' # You don't need to change this
token = 'oauth:43rip6j6fgio8n5xly1oum1lph8ikl1' # get it from https://twitchapps.com/tmi/.
user = 'ardha27' # Your Twitch username
channel = '#aikohound' # The channel you want to retrieve messages from
```

6. Choose which TTS you want to use, `VoiceVox` or `Silero`. Uncomment and Comment to switch between them

```
# Choose between the available TTS engines
# Japanese TTS
voicevox_tts(tts)

# Silero TTS, Silero TTS can generate English, Russian, French, Hindi, Spanish, German, etc. Uncomment the line below. Make sure the input is in that language
# silero_tts(tts_en, "en", "v3_en", "en_21")
```

7. Install VoiceVox Docker 

You can download VoiceVox Docker on this website: https://www.docker.com/products/docker-desktop/

8. Sound available online

You can check available sound on this website: https://voicevox.hiroshiba.jp/ 

You can check the sound used on TTS.py

9. If you want to use the audio output from the program as an input for your `Vtubestudio`. You will need to capture your desktop audio using `Virtual Cable` and use it as input on VtubeStudio microphone.

10. If you planning to use this program for live streaming Use `chat.txt` and `output.txt` as an input on OBS Text for Realtime Caption/Subtitles

11. Usage instruction

After finishing all the repairation, open the instruction.docx to use the code  

## Credits

This project is inspired by the work of Ardha. Special thanks to the creators of the technologies used in this project including VoiceVox Engine, DeepL, Gemini, and VtubeStudio.
