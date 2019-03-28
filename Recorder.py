import subprocess

import pyaudio
import time

import shutil

import Audio_Utils
from Sound import SoundEntry


class AudioRecorder:
    def __init__(self, soundCollection):
        self.frames = []
        self.previous_recordings = []
        self.record_start = None
        self.record_end = None
        self.curr_index = 0
        self.soundCollection = soundCollection

    def listen(self):
        stream = pyaudio.PyAudio().open(
            format=pyaudio.paInt16,
            channels=2,
            rate=44100,
            input=True,
            frames_per_buffer=1024,
            input_device_index=Audio_Utils.getIndexOfStereoMix()
        )

        while True:
            read_result = stream.read(1024)
            if len(self.frames) > Audio_Utils.secondsToFrames(60) and self.record_start is None: # every 60 seconds, reset the size of our frame array UNLESS we are currently recording something (record_start gets set to a number if we are)
                print "removing all but last 10 seconds of frames. Frame size went from " + str(len(self.frames)) + " to " + str(len(self.frames[-Audio_Utils.secondsToFrames(10):]))
                self.frames = self.frames[-Audio_Utils.secondsToFrames(10):]
            self.frames.append(read_result)


    def processKeysDown(self, keys_down_tuple):
        if len(keys_down_tuple) >= 2:
            if keys_down_tuple[0] == "menu" and keys_down_tuple[1] == "x":
                if self.record_start is None: # if we aren't already recording
                    self.startRecording()
                else:
                    self.stopRecording()
                    self.curr_index = len(self.previous_recordings)-1
                    self.updateSoundboardWithCurrRecording()

            elif keys_down_tuple[0] in "1234567890" and keys_down_tuple[1] == "end":
                new_file_name = "x" + keys_down_tuple[0] + ".wav"
                shutil.copyfile("x.wav", new_file_name)
                self.soundCollection.key_bind_map[frozenset([keys_down_tuple[0], "next"])] = SoundEntry(new_file_name)
                subprocess.Popen(["audacity.exe", new_file_name], executable="D:/Program Files (x86)/Audacity/audacity.exe")


    # def toggleRecording(self):
    #     if self.record_start is None: # if we aren't already recording
    #         self.startRecording()
    #     else:
    #         self.stopRecording()

    def startRecording(self):
        self.record_start = len(self.frames)-1 # save index of current frame

    def stopRecording(self):
        time.sleep(.25)
        self.record_end = len(self.frames)-1 # save index of where we stopped recording
        frames_to_save = list(self.frames[self.record_start:self.record_end])
        normalized_frames_to_save = Audio_Utils.getNormalizedAudioFrames(frames_to_save, Audio_Utils.DEFAULT_DBFS)
        normalized_frames_to_save = Audio_Utils.getFramesWithoutStartingSilence(normalized_frames_to_save)
        print "recorded",  '%.2f' % Audio_Utils.framesToSeconds(self.record_end-self.record_start), "seconds of audio"
        self.record_start = None
        self.record_end = None
        if len(self.previous_recordings) >= 5:
            del(self.previous_recordings[0])
        self.previous_recordings.append(normalized_frames_to_save)

    def selectPrevRecording(self):
        self.curr_index -= 1
        if self.curr_index < 0:
            self.curr_index = len(self.previous_recordings)-1
        self.updateSoundboardWithCurrRecording()

    def selectNextRecording(self):
        self.curr_index += 1
        if self.curr_index >= len(self.previous_recordings):
            self.curr_index = 0
        self.updateSoundboardWithCurrRecording()

    def deleteCurrRecording(self):
        if len(self.previous_recordings) > 0:
            del self.previous_recordings[self.curr_index]
            self.selectPrevRecording()

    def getLastRecordingContents(self):
        return self.previous_recordings[-1]

    def getNthLastRecording(self, n):
        return self.previous_recordings[-n]

    def updateSoundboardWithCurrRecording(self):
        recording_contents = self.previous_recordings[self.curr_index]
        self.soundCollection.getSoundEntryByName("x.wav").frames = recording_contents
        Audio_Utils.writeFramesToFile(recording_contents, "x.wav")