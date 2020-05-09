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


def writeFramesToFile(frames, filename, backup_old_sound, normalize=True):
    if backup_old_sound and os.path.exists(filename):
        copyfileToBackupFolder(filename)
    wf = wave.open(filename, 'wb')
    try:
        wf.setnchannels(Const.CHANNELS)
        wf.setsampwidth(Const.SAMPLE_WIDTH)
        wf.setframerate(Const.FRAME_RATE)
        if normalize:
            frames = getNormalizedAudioFrames(frames, DEFAULT_DBFS)
        wf.writeframes(b''.join(frames))
    finally:
        wf.close()

def getFramesFromFile(filename):
    try:
        if os.path.exists(filename):
            wf = wave.open(filename, 'rb')
            frames = []
            frame = wf.readframes(64)
            while frame != '':
                frames.append(frame)
                frame = wf.readframes(64)
            wf.close()
            return frames
        else:
            raise ValueError("error: read from from file because file does not exist\tfilename=" + str(filename))
    except:
        print "failed to getFramesFromfile for filename"+filename


def getReversedFrames(frames):
    reversed_frames = []
    for frame in frames:
        reversed_frame = getReversedFrame(frame)
        reversed_frames.append(reversed_frame)
    return reversed_frames[::-1]

def getReversedFrame(frame):
    atomic_audio_units = unpackFrameIntoAtomicAudioUnits(frame)
    atomic_audio_units = atomic_audio_units[::-1]
    return buildFrameFromAtomicAudioUnits(atomic_audio_units)


def unpackFrameIntoAtomicAudioUnits(frame):
    atomic_audio_units = []
    # assuming stereo and 16bit int wav sound, atomic audio unit contains 4 str chars
    # first 2 chars represent audio for channel 1, second 2 chars represent audio for channel 2

    # unpack the str into atomic audio units (4 bytes or 4 chars) by zipping every 4 chars into a tuple
    frame_iter = iter(frame)
    frame_zipped_into_atomic_audio_units = zip(frame_iter, frame_iter, frame_iter, frame_iter)

    for zipped in frame_zipped_into_atomic_audio_units:
        unzipped_atomic_audio_unit = zipped[0] + zipped[1] + zipped[2] + zipped[3]
        atomic_audio_units.append(unzipped_atomic_audio_unit)

    return atomic_audio_units

def buildFrameFromAtomicAudioUnits(atomic_wav_bytes):
    new_frame = ''
    for atomic_audio_chunk in atomic_wav_bytes:
        new_frame += atomic_audio_chunk

    return new_frame

def getNormalizedAudioFrames(frames, target_dBFS):
    sound = AudioSegment(b''.join(frames), sample_width=Const.SAMPLE_WIDTH, frame_rate=Const.FRAME_RATE, channels=Const.CHANNELS)
    normalized_sound = getSoundWithMatchedAmplitude(sound, target_dBFS)
    return byteStringToFrameList(normalized_sound.raw_data)

def byteStringToFrameList(bytes):
    '''
    :param bytes: str
    :return: list(str)
    '''
    frames = []
    for i in range(0, len(bytes), Const.FRAMES_PER_BUFFER/4):
        frames.append(bytes[i:i+Const.FRAMES_PER_BUFFER/4])
    return frames


def getSoundWithMatchedAmplitude(sound, target_dBFS):
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound.apply_gain(change_in_dBFS)

def copyfileToBackupFolder(filename, folder=None):
    if folder == None:
        if "manual_record" in filename:
            folder = "Manual_Records"
        else:
            folder = "Audio_Backups"
    formatted_date = str(datetime.datetime.now()).split('.')[0].replace(":", "_")
    number_of_bytes_in_one_second_of_audio = float(198656) # kind of arbitrary, I calculated it from one of my files
    seconds_in_file_formatted_nicely = str(round(os.path.getsize(filename)/number_of_bytes_in_one_second_of_audio, 1)).replace(".", ",")
    shutil.copyfile(filename, folder + "/" + filename.replace(".wav", "") + " " + seconds_in_file_formatted_nicely + " seconds - " + formatted_date + ".wav")

def getPitchShiftedFrame(frame, octaves):
    sample_width = pyaudio.PyAudio().get_sample_size(pyaudio.paInt16)
    sound = AudioSegment(frame, sample_width=sample_width, frame_rate=44100, channels=2)

    new_sample_rate = int(sound.frame_rate * (2.0 ** octaves))
    lowpitch_sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
    lowpitch_sound = lowpitch_sound.set_frame_rate(44100)

    return lowpitch_sound.raw_data



def secondsToFrames(number_of_seconds):
    return int(number_of_seconds * 690) # 690 is an estimation I calculated, correct within a few ms

def framesToSeconds(number_of_frames):
    return number_of_frames / 690.0 # 690 is an estimation I calculated, correct within a few ms

def getVolumeOfFrame(frame):
    return max(array.array('h', frame))
    # return sum(array.array('h', frame)) / len(array.array('h', frame))

def getFramesWithoutStartingSilence(frames):
    for i in range(0, len(frames)):
        volume = getVolumeOfFrame(frames[i])
        if volume > SILENCE_THRESHOLD:
            return frames[i:]

    return frames



