from pydub import AudioSegment
import pydub.playback
import wave
import os
import shutil
import datetime
import struct
import pyaudio
import numpy as np
import io

DEFAULT_DBFS = -20.0


def writeFramesToFile(frames, filename, normalize=True):
    if os.path.exists(filename) and "Extended_Audio" not in filename:
        copyfileToBackupFolder(filename)
        os.remove(filename)
    wf = wave.open(filename, 'wb')
    wf.setnchannels(2)
    wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
    wf.setframerate(44100)
    if normalize:
        frames = getNormalizedAudioFrames(frames, DEFAULT_DBFS)
    wf.writeframes(b''.join(frames))
    wf.close()



def getFramesFromFile(filename):
    if os.path.exists(filename):
        wf = wave.open(filename, 'rb')
        frames = []
        frame = wf.readframes(1024)
        while frame != '':
            frames.append(frame)
            frame = wf.readframes(1024)
        wf.close()
        return frames
    else:
        print "error: cannot write file to frames because file does not exist\tfilename=" + str(filename)




def getNormalizedAudioFrames(frames, target_dBFS):
    sample_width = pyaudio.PyAudio().get_sample_size(pyaudio.paInt16)
    sound = AudioSegment(b''.join(frames), sample_width=sample_width, frame_rate=44100, channels=2)
    normalized_sound = getSoundWithMatchedAmplitude(sound, target_dBFS)
    normalized_sound_as_bytestring = normalized_sound.raw_data
    normalized_bytestream_as_frame_list = [normalized_sound_as_bytestring[i:i+1024] for i in range(0, len(normalized_sound_as_bytestring), 1024)] # slice bystestring into chunks of 1024 bytes
    return normalized_bytestream_as_frame_list

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


def trimEnd(infile, outfilename, trim_ms):
    infile = wave.open(infile, "r")
    width = infile.getsampwidth()
    rate = infile.getframerate()
    frameCount = infile.getnframes()
    fpms = rate / 1000 # frames per ms
    length = frameCount - (trim_ms*fpms)

    out = wave.open("_"+outfilename, "w")
    out.setparams((infile.getnchannels(), width, rate, length, infile.getcomptype(), infile.getcompname()))

    out.writeframes(infile.readframes(length))
    out.close()
    infile.close()

    shutil.move("_"+outfilename, outfilename)


def trimStart(infile, outfilename, trim_ms):
    infile = wave.open(infile, "r")
    width = infile.getsampwidth()
    rate = infile.getframerate()
    frameCount = infile.getnframes()
    fpms = rate / 1000 # frames per ms
    length = frameCount - (trim_ms*fpms)
    start_index = trim_ms * fpms

    infile.rewind()
    anchor = infile.tell()
    infile.setpos(anchor + start_index)


    out = wave.open("_"+outfilename, "w")
    out.setparams((infile.getnchannels(), width, rate, length, infile.getcomptype(), infile.getcompname()))

    out.writeframes(infile.readframes(length))
    out.close()
    infile.close()

    shutil.move("_"+outfilename, outfilename)


def getIndexOfStereoMix():
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
    print 'WARNING: failed to find stereo mix. using default input device "' + default_device['name'] + ' at index ' + str(default_device['index'])
    return default_device['index']

def getIndexOfSpeakers():
    speakers_info = pyaudio.PyAudio().get_default_output_device_info()
    print 'found speakers "', speakers_info['name'], 'at index ', speakers_info['index']
    return speakers_info['index']

def getIndexOfVirtualAudioCable():
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



def getPitchShiftedFrame(frame, octaves):
    sample_width = pyaudio.PyAudio().get_sample_size(pyaudio.paInt16)
    sound = AudioSegment(frame, sample_width=sample_width, frame_rate=44100, channels=2)

    new_sample_rate = int(sound.frame_rate * (2.0 ** octaves))
    lowpitch_sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
    lowpitch_sound = lowpitch_sound.set_frame_rate(44100)

    return lowpitch_sound.raw_data

def secondsToFrames(seconds):
    return int(seconds*43)

def framesToSeconds(frames):
    return '%.2f' % (float(frames)/43)
