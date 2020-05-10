from pydub import AudioSegment, effects
import wave
import os
import shutil
import datetime
import pyaudio
from stream import Const
import array

DEFAULT_DBFS = -20.0
SILENCE_THRESHOLD = 500
FRAMES_PER_CHUNK = 64

FRAME_SIZE_IN_BYTES = 4
CHUNK_SIZE_IN_FRAMES = 64


'''
https://developer.apple.com/documentation/coreaudiotypes/audiostreambasicdescription?language=objc
 - A sample is single numerical value for a single audio channel in an audio stream.
 - A frame is a collection of time-coincident samples. For instance, a linear PCM stereo sound file
   has two samples per frame, one for the left channel and one for the right channel.
 - A chunk is a collection of one or more contiguous frames.

'''

def writeChunksToFile(chunks, filename, backup_old_sound, normalize=True):
    if backup_old_sound and os.path.exists(filename):
        copyfileToBackupFolder(filename)
    wf = wave.open(filename, 'wb')
    try:
        wf.setnchannels(Const.CHANNELS)
        wf.setsampwidth(Const.SAMPLE_WIDTH)
        wf.setframerate(Const.FRAME_RATE)
        if normalize:
            chunks = getNormalizedAudioChunks(chunks, DEFAULT_DBFS)
        wf.writeframes(b''.join(chunks))
    finally:
        wf.close()

def getChunksFromFile(filename):
    try:
        if os.path.exists(filename):
            wf = wave.open(filename, 'rb')
            chunks = []
            frames = wf.readframes(4096)
            while frames != '':
                chunks += packFramesIntoChunks(frames)
                frames = wf.readframes(4096)
            wf.close()
            return chunks
        else:
            raise ValueError("error: read from from file because file does not exist\tfilename=" + str(filename))
    except:
        print "failed to getChunksFromfile for filename"+filename

def packFramesIntoChunks(frames):
    '''
    takes a big bytestring of frames, and breaks it into chunks
    :param frames: str
    :return: list(str)
    '''
    chunks = []
    rem = len(frames) % CHUNK_SIZE_IN_FRAMES
    for i in range(0, len(frames)-rem, CHUNK_SIZE_IN_FRAMES):
        chunks.append(frames[i:i+CHUNK_SIZE_IN_FRAMES])
    return chunks



def getReversedChunks(chunks):
    reversed_chunks = []
    for chunk in chunks:
        reversed_chunk = getReversedChunk(chunk)
        reversed_chunks.append(reversed_chunk)
    return reversed_chunks[::-1]

def getReversedChunk(chunk):
    '''
    Take each chunk, separate it into frames, reverse the order of the frames, then convert it back into a chunk
    e.g. [1,2,3,4,5,6,7,8] -> [ [1,2,3], [4,5,6], [7,8,9] ] -> [ [3,2,1], [6,5,4], [9,8,7]] -> [3,2,1,6,5,4,9,8,7]
    :param chunk: string
    :return: string
    '''
    frames = unpackChunkIntoFrames(chunk)
    frames = frames[::-1]
    return ''.join(frames)


def unpackChunkIntoFrames(chunk):
    '''
    Assuming stereo and 16bit int wav sound, each frame contains 4 str chars
    First 2 chars represent the sample for channel 1, second 2 chars represent the sample for channel 2
    We get the frames by grouping every 4 str chars of the audio chunk into a frame, then returning the list
    :param chunk: str
    '''
    if len(chunk) % 4 != 0:
        raise Exception("ERROR: expected audio chunk to be made up of groups of 4 str chars (maybe its mono instead of stereo?)")

    frames = []
    for i in range(0, len(chunk), 4):
        frames.append(chunk[i:i + 4])
    return frames

def getNormalizedAudioChunks(chunks, target_dBFS):
    sound = AudioSegment(b''.join(chunks), sample_width=Const.SAMPLE_WIDTH, frame_rate=Const.FRAME_RATE, channels=Const.CHANNELS)
    normalized_sound = getSoundWithMatchedAmplitude(sound, target_dBFS)
    return packFramesIntoChunks(normalized_sound.raw_data)


def getSoundWithMatchedAmplitude(sound, target_dBFS):
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound.apply_gain(change_in_dBFS)

def copyfileToBackupFolder(filename, folder=None):
    if folder is None:
        if "manual_record" in filename:
            folder = "Manual_Records"
        else:
            folder = "Audio_Backups"
    formatted_date = str(datetime.datetime.now()).split('.')[0].replace(":", "_")
    number_of_bytes_in_one_second_of_audio = float(198656) # kind of arbitrary, I calculated it from one of my files
    seconds_in_file_formatted_nicely = str(round(os.path.getsize(filename)/number_of_bytes_in_one_second_of_audio, 1)).replace(".", ",")
    shutil.copyfile(filename, folder + "/" + filename.replace(".wav", "") + " " + seconds_in_file_formatted_nicely + " seconds - " + formatted_date + ".wav")

def getPitchShiftedChunk(chunk, octaves):
    sample_width = pyaudio.PyAudio().get_sample_size(pyaudio.paInt16)
    sound = AudioSegment(chunk, sample_width=sample_width, frame_rate=44100, channels=2)

    new_sample_rate = int(sound.frame_rate * (2.0 ** octaves))
    lowpitch_sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
    lowpitch_sound = lowpitch_sound.set_frame_rate(44100)

    return lowpitch_sound.raw_data



def secondsToChunks(number_of_seconds):
    return int(number_of_seconds * 690) # 690 is an estimation I calculated, correct within a few ms

def chunksToSeconds(number_of_chunks):
    return number_of_chunks / 690.0 # 690 is an estimation I calculated, correct within a few ms

def getVolumeOfChunk(chunk):
    return max(array.array('h', chunk))

def getChunksWithoutStartingSilence(chunks, silence_threshold=SILENCE_THRESHOLD):
    for i in range(0, len(chunks)):
        volume = getVolumeOfChunk(chunks[i])
        if volume > silence_threshold:
            return chunks[i:]
    return []



