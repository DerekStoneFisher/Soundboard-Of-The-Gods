import pyaudio

FORMAT=pyaudio.paInt16
CHANNELS=2
FRAME_RATE=44100
INPUT=True
FRAMES_PER_BUFFER=1024
OUTPUT=True
OUTPUT_DEVICE_INDEX=2
SAMPLE_WIDTH=pyaudio.PyAudio().get_sample_size(pyaudio.paInt16)