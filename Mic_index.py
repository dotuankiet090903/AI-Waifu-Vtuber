import pyaudio

p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info.get('maxInputChannels', 0) > 0:
        print(f"[{i}] {info['name']} - channels: {info['maxInputChannels']} - rate: {int(info['defaultSampleRate'])}")
p.terminate()
