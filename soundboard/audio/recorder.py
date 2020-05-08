import subprocess
from collections import OrderedDict
import pyaudio
import time
import thread
import shutil

import Audio_Utils
from Sound import SoundEntry
from stream import StreamBuilder
import os
import uuid

DELETED_FILES_FOLDER = "D:/Projects/Audio-Shadow-Play-Git/deleted_files"

class RecordingManager:
    def __init__(self, recordings_folder, sound_entry_to_write_to):
        '''

        :param recordings_folder: str
        :param sound_entry_to_write_to: SoundEntry
        '''
        self.sound_entry_to_write_to = sound_entry_to_write_to
        self.recordings_folder = recordings_folder
        self.recorder = AudioRecorder()
        self.recording_names_to_frames = OrderedDict()

        self.recording_names = [f for f in os.listdir(recordings_folder) if f.endswith('.wav')]
        self.recording_names.sort(key=lambda x: os.path.getmtime(os.path.join(recordings_folder, x)))
        self.current_index = len(self.recording_names)-1

        self._preemptivelyLoadFramesForNextFewRecordings()

    def toggleRecord(self, auto_save=True):
        if not self.recorder.isRecording():
            self.recorder.startRecording()
        else:
            self.recorder.stopRecording()
            saved_frames = self.recorder.getSavedFramesFromRecording()

            recording_name = "recording " + str(uuid.uuid4()) + '.wav'
            self.recording_names.append(recording_name)
            self.current_index = len(self.recording_names)-1
            self.recording_names_to_frames[recording_name] = saved_frames
            self.sound_entry_to_write_to.frames = saved_frames

            if auto_save:
                self.saveCurrentRecordingToFile()

    def deleteCurrentRecording(self):
        recording_name = self.recording_names[self.current_index]
        del self.recording_names_to_frames[recording_name]
        del self.recording_names[self.current_index]

        if self.current_index != 0:
            self.current_index -= 1
        recording_path = os.path.join(self.recordings_folder, recording_name)
        if os.path.exists(recording_path):
            os.rename(recording_path, os.path.join(DELETED_FILES_FOLDER, recording_name))
        self._updateSoundCollection()

    def refreshRecording(self):
        self.sound_entry_to_write_to.frames = self.recorder.getSavedFramesFromRecording()

    def renameCurrentRecording(self):
        old_recording_name = self.recording_names[self.current_index]
        recording_frames = self.recording_names_to_frames[old_recording_name]

        new_name = raw_input("Enter new name for recording '" + old_recording_name + "'. (adding '.wav' is optional)")
        if not new_name.endswith('.wav'):
            new_name = new_name + '.wav'

        if new_name != old_recording_name:
            del self.recording_names_to_frames[old_recording_name]
            self.recording_names_to_frames[new_name] = recording_frames
            self.recording_names[self.current_index] = new_name
            self.saveCurrentRecordingToFile(overwrite=True)
            old_path = os.path.join(self.recordings_folder, old_recording_name)
            if os.path.exists(old_path):
                os.rename(old_path, os.path.join(DELETED_FILES_FOLDER, old_recording_name))

    def saveCurrentRecordingToFile(self, overwrite=False):
        recording_name = self.recording_names[self.current_index]
        recording_frames = self.recording_names_to_frames[recording_name]
        recording_path = os.path.join(self.recordings_folder, recording_name)
        if not os.path.exists(recording_path) or overwrite:
            thread.start_new_thread(Audio_Utils.writeFramesToFile, (recording_frames, recording_path, False))

    def loadNextRecording(self):
        if self.current_index >= len(self.recording_names):
            self.current_index = 0
        else:
            self.current_index += 1
        self._updateSoundCollection()

    def loadPreviousRecording(self):
        if self.current_index < 0:
            self.current_index = len(self.recording_names)-1
        else:
            self.current_index -= 1
        self._updateSoundCollection()

    def _updateSoundCollection(self):
        self._preemptivelyLoadFramesForNextFewRecordings()
        recording_name = self.recording_names[self.current_index]
        self.sound_entry_to_write_to.frames = self._getFramesFromRecordingName(recording_name)

    def _getFramesFromRecordingName(self, name):
        if name not in self.recording_names_to_frames:
            path = os.path.join(self.recordings_folder, name)
            self.recording_names_to_frames[name] = Audio_Utils.getFramesFromFile(path)
        return self.recording_names_to_frames[name]

    def _preemptivelyLoadFramesForNextFewRecordings(self):
        for i in range(self.current_index-5, self.current_index+5):
            if 0 < i < len(self.recording_names):
                thread.start_new_thread(self._getFramesFromRecordingName, (self.recording_names[i],))

class AudioRecorder:
    def __init__(self):
        '''
        An "always recording recorder". Call toggleRecording once to start recording, then call it again to end the recording.
        '''
        self._listen_frames_snapshot = [] # what _listen_frames looked like when the last recording ended
        self._listen_frames = [] # temporary frames always being recorded to
        self._start_index = None # index of first recording frame.
        self._end_index = None # index of final recording frame.
        self._is_recording = False

        thread.start_new_thread(self._listen, tuple())

    def isRecording(self):
        return self._is_recording

    def _listen(self):
        '''
        Listens in an endless loop, updating frames as it listens.
        Spawn a thread to call this method or it will block you permanently.
        :return: None
        '''
        stream = StreamBuilder().getInputStream(StreamBuilder.STEREO_MIX_INDEX)
        while True:
            read_result = stream.read(1024)
            # If we aren't in the middle of a recording, chop the last minute off of our listening frames every 2 minutes
            if len(self._listen_frames) > Audio_Utils.secondsToFrames(120) and self._start_index is None:
                print "removing first 60 seconds of frames. Frame size went from " + str(len(self._listen_frames)) \
                      + " to " + str(len(self._listen_frames[-Audio_Utils.secondsToFrames(10):]))
                self._listen_frames = self._listen_frames[-Audio_Utils.secondsToFrames(60):]
            self._listen_frames.append(read_result)

    def startRecording(self):
        print "recording started"
        self._is_recording = True
        self._start_index = len(self._listen_frames)-1 # save index of current frame
        self._end_index = None

    def stopRecording(self):
        self._is_recording = False
        time.sleep(.25) # this just feels right - recordings won't cut off as much with this
        self._end_index = len(self._listen_frames)-1 # save index of where we stopped recording
        self._listen_frames_snapshot = list(self._listen_frames) # save a copy of how the frames looked when we stopped recording
        print "recorded",  '%.2f' % Audio_Utils.framesToSeconds(self._end_index - self._start_index), "seconds of audio"

    def getSavedFramesFromRecording(self):
        '''
        Takes the frames between the start and end of the recording and saves them to saved_frames.
        Normalizes the volume and trims the starting silence first.
        :return: None
        '''
        if None in [self._start_index, self._end_index]:
            print "cannot save recording until a recording has been started and stopped"
            return
        frames_to_save = list(self._listen_frames_snapshot[self._start_index:self._end_index])
        normalized_frames_to_save = Audio_Utils.getNormalizedAudioFrames(frames_to_save, Audio_Utils.DEFAULT_DBFS)
        return Audio_Utils.getFramesWithoutStartingSilence(normalized_frames_to_save)

    def moveRecordingStartBack(self, seconds_to_extend):
        '''
        if you started recording too late and missed something, use this to
        move back the start time of the recording.
        :param seconds_to_extend: float
        :return: None
        '''
        if self._start_index is not None:
            frames_to_extend = Audio_Utils.secondsToFrames(seconds_to_extend)
            self._start_index = max((0, self._start_index - frames_to_extend))

    def moveRecordingStartForward(self, seconds_to_extend):
        '''
        Does the opposite of moveRecordingStartBack.
        :param seconds_to_extend: float
        :return: None
        '''
        if self._start_index is not None:
            frames_to_extend = Audio_Utils.secondsToFrames(seconds_to_extend)
            self._start_index = min((len(self._listen_frames_snapshot)-1, self._start_index + frames_to_extend))
