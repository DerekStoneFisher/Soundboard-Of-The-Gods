import pyaudio

FORMAT=pyaudio.paInt16
CHANNELS=2
FRAME_RATE=44100
FRAMES_PER_BUFFER=1024
SAMPLE_WIDTH=pyaudio.PyAudio().get_sample_size(pyaudio.paInt16)