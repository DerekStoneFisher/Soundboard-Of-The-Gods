import pyaudio, threading

class Const(object):
    CHANNELS = 2
    FORMAT = pyaudio.paInt16
    FRAME_RATE = 44100
    FRAMES_PER_BUFFER = 1024
    SAMPLE_WIDTH = pyaudio.PyAudio().get_sample_size(pyaudio.paInt16)

class SharedStream:
    '''
    one soundEntry can play sounds to SharedStream at a time
    A sharedStream usually has 1 stream for the primary output device (speaker) and 1 stream for the virtual audio cable.
    '''
    def __init__(self):
        self.in_use = False
        self.output_streams = self._initializeAndReturnOutputStreams()

    def playChunk(self, chunk):
        for stream in self.output_streams:
            stream.write(chunk)

    def _initializeAndReturnOutputStreams(self):
        output_streams = []

        # Add the primary output stream (default output device)
        speaker_stream = StreamBuilder().getOutputStream(StreamBuilder.SPEAKERS_INDEX)
        output_streams.append(speaker_stream)

        # add the secondary output stream if available (virtual audio cable output)
        virtual_speaker_stream = StreamBuilder().getOutputStream(StreamBuilder.VIRTUAL_AUDIO_CABLE_INDEX)
        if virtual_speaker_stream and virtual_speaker_stream != speaker_stream:
            output_streams.append(virtual_speaker_stream)
        return output_streams


class StreamBuilder:
    SPEAKERS_INDEX = None
    VIRTUAL_AUDIO_CABLE_INDEX = None
    STEREO_MIX_INDEX = None

    initialized_indices = False

    def __init__(self):
        '''
        A semi-utilties class which:
         - Contains public methods getOutputStream and getInputStream which create and return pyaudio streams.
         - determines and stores SPEAKERS_INDEX, VIRTUAL_AUDIO_CABLE_INDEX, and STEREO_MIX_INDEX
         - stores stream constants such as channel count, pyaudio format, and frames per buffer
        '''
        this = StreamBuilder
        if not this.initialized_indices:
            this.SPEAKERS_INDEX = this._getIndexOfSpeakers()
            this.VIRTUAL_AUDIO_CABLE_INDEX = this._getIndexOfVirtualAudioCable()
            this.STEREO_MIX_INDEX = this._getIndexOfStereoMix()
            this.initialized_indices = True

    def getOutputStream(self, output_device_index=SPEAKERS_INDEX):
        '''
        creates and returns a pyaudio output stream assigned to the device index passed in.
        use static class vars SPEAKERS_INDEX or VIRTUAL_AUDIO_CABLE_INDEX as indexes
        :param output_device_index: int
        :return: A new :py:class:`Stream`
        '''
        if output_device_index is None:
            print "getOutputStream passed a null output_device_index, so it is returning null"
            return None

        this = StreamBuilder
        return pyaudio.PyAudio().open(
            format=Const.FORMAT,
            channels=Const.CHANNELS,
            rate=Const.FRAME_RATE,
            frames_per_buffer=Const.FRAMES_PER_BUFFER,
            output=True,
            output_device_index=output_device_index
        )

    def getInputStream(self, input_device_index=STEREO_MIX_INDEX):
        '''
        creates and returns a pyaudio input stream assigned to the device index passed in.
        use static class var STEREO_MIX_INDEX if not sure what device index to use
        :param input_device_index: int
        :return: A new :py:class:`Stream`
        '''
        if input_device_index is None:
            print "getInputStream passed a null input_device_index, so it is returning null"
            return None
        return pyaudio.PyAudio().open(
            format=Const.FORMAT,
            channels=Const.CHANNELS,
            rate=Const.FRAME_RATE,
            input=True,
            frames_per_buffer=Const.FRAMES_PER_BUFFER,
            input_device_index=input_device_index
        )

    @staticmethod
    def _getIndexOfStereoMix():
        p = pyaudio.PyAudio()
        device_count = p.get_device_count()
        print "searching for stereo mix..."
        for i in range(0, device_count):
            current_device = p.get_device_info_by_index(i)
            device_name = current_device["name"]
            device_index = current_device["index"]
            is_input_device = current_device["maxInputChannels"] > 0
            if is_input_device and 'Stereo Mix' in device_name:
                print 'found stereo mix "' + device_name + '" at index ' + str(device_index)
                return device_index
        default_device = p.get_default_input_device_info()
        print 'WARNING: failed to find stereo mix. using default input device "' + default_device[
            'name'] + ' at index ' + str(default_device['index'])
        return default_device['index']

    @staticmethod
    def _getIndexOfSpeakers():
        speakers_info = pyaudio.PyAudio().get_default_output_device_info()
        print 'found speakers "', speakers_info['name'], 'at index ', speakers_info['index']
        return speakers_info['index']

    @staticmethod
    def _getIndexOfVirtualAudioCable():
        p = pyaudio.PyAudio()
        device_count = p.get_device_count()
        print "searching for virtual audio cable..."
        for i in range(0, device_count):
            current_device = p.get_device_info_by_index(i)
            device_name = current_device["name"]
            device_index = current_device["index"]
            is_output_device = current_device["maxOutputChannels"] > 0
            if is_output_device and ("cable" in device_name.lower() or "virtual" in device_name.lower()):
                print 'found virtual audio cable "' + device_name + '" at index ' + str(device_index)
                return device_index
        print "WARNING: failed to find virtual audio cable... Soundboard will not be audible over the microphone, only through your speakers."
        return None



class SharedStreamCollection:
    def __init__(self, stream_count=10):
        self.shared_streams = [SharedStream() for _ in range(0, stream_count)]

    def getUnusedStreamAndIndex(self):
        '''
        the SoundEntry that calls this function is responsible for saving the index of the stream and
        calling releaseStreamAtIndex with that index when done with the stream
        :return: SoundEntry, int
        '''
        for i, stream in enumerate(self.shared_streams):
            if not stream.in_use:
                stream.in_use = True
                return stream, i

        print "could not find a free stream, adding a new one and returning that one"
        self.shared_streams.append(SharedStream())
        return self.shared_streams[-1]

    def releaseStreamAtIndex(self, index):
        self.shared_streams[index].in_use = False

class SharedStreamManager(object):
    lock = threading.Lock()
    shared_streams = SharedStreamCollection()

    @classmethod
    def getUnusedStreamAndIndex(cls):
        with cls.lock:
            return cls.shared_streams.getUnusedStreamAndIndex()

    @classmethod
    def releaseStreamAtIndex(cls, index):
        with cls.lock:
            return cls.shared_streams.releaseStreamAtIndex(index)

