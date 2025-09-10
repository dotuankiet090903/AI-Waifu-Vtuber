import pyaudio

def list_input_devices():
    p = pyaudio.PyAudio()
    print("=== Input devices ===")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info.get('maxInputChannels', 0) > 0:
            host_api = p.get_host_api_info_by_index(info['hostApi'])['name']
            print(f"[{i}] {info['name']} | hostApi={host_api} | "
                  f"channels={info['maxInputChannels']} | defaultRate={int(info['defaultSampleRate'])}")
    p.terminate()


list_input_devices()

import pyaudio, wave, audioop, time

def test_record_wav(device_index=None, seconds=5, out_path="input.wav"):
    p = pyaudio.PyAudio()

    if device_index is None:
        try:
            device_index = p.get_default_input_device_info()['index']
        except Exception:
            device_index = None

    if device_index is None:
        raise RuntimeError("No default input device. Run list_input_devices() and pass a device_index.")

    dev = p.get_device_info_by_index(device_index)
    RATE = int(dev.get('defaultSampleRate', 16000))  # use device default
    CHANNELS = 1                                     # mono is fine for speech
    FORMAT = pyaudio.paInt16
    CHUNK = 1024

    print(f"Recording {seconds}s from device [{device_index}] {dev['name']} at {RATE} Hz...")
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    input_device_index=device_index)

    frames = []
    start = time.time()
    while time.time() - start < seconds:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
        # tiny VU meter: if it never changes, you're probably getting silence
        level = audioop.rms(data, 2)  # 2 bytes/sample for paInt16
        print(f"\rLevel: {level:5d}", end="")

    print("\nStopped.")
    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(out_path, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))

    print(f"Wrote {out_path}. Play it—do you hear yourself?")

test_record_wav(device_index=2, seconds=5)
