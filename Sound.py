import Audio_Utils
import pyaudio
import json
from Audio_Proj_Const import KEY_ID_TO_NAME_MAP, convertJavaKeyIDToRegularKeyID
import os
import time, thread



class SoundCollection:
    def __init__(self, key_bind_map=None):
        self.key_bind_map = key_bind_map
        if self.key_bind_map is None:
            self.key_bind_map = dict()
            if os.path.exists("x.wav"):
                self.key_bind_map[frozenset(['control','multiply'])] = SoundEntry("x.wav")
            for number in "1234567890":
                file_name = "x" + number + ".wav"
                if os.path.exists(file_name):
                    self.key_bind_map[frozenset([number, "next"])] = SoundEntry(file_name)

    def ingestSoundboardJsonConfigFile(self, config_file_path):
        with open(config_file_path) as config_file:
            config_object = json.load(config_file)
            soundboard_entries = config_object["soundboardEntries"]
            for soundboard_entry in soundboard_entries:
                try:
                    path_to_sound_file = soundboard_entry["file"]
                    activation_key_codes = soundboard_entry["activationKeysNumbers"]
                    if os.path.exists(path_to_sound_file):
                        activation_key_names = [KEY_ID_TO_NAME_MAP[convertJavaKeyIDToRegularKeyID(key_code)].lower() for key_code in activation_key_codes]
                        soundEntry_to_add = SoundEntry(path_to_sound_file, activation_keys=frozenset(activation_key_names))
                        self.key_bind_map[frozenset(activation_key_names)] = soundEntry_to_add
                except:
                    print "failed to ingest", soundboard_entry["file"]


    def addSoundEntry(self, soundEntry):
        copy = frozenset(soundEntry.activation_keys)
        self.key_bind_map[copy] = soundEntry

    def stopAllSounds(self):
        for soundEntry in self.key_bind_map.values():
            soundEntry.stop()

    def resetAllPitches(self):
        for soundEntry in self.key_bind_map.values():
            soundEntry.pitch_modifier = 0

    def shiftAllPitches(self, shift_amount):
        for soundEntry in self.key_bind_map.values():
            soundEntry.pitch_modifier += shift_amount

    def addSoundEntries(self, soundEntries):
        for soundEntry in soundEntries:
            self.addSoundEntry(soundEntry)

    def getBestSoundEntryMatchOrNull(self, keys_down):
        keys_down = list(keys_down) # make a mutable copy that won't change the original
        while len(keys_down) != 0:
            if frozenset(keys_down) in self.key_bind_map:
                return self.key_bind_map[frozenset(keys_down)]
            else:
                del(keys_down[0])
        return None

    def getSoundEntryByName(self, name_of_sound):
        for sound_entry in self.key_bind_map.values():
            if os.path.basename(sound_entry.path_to_sound).lower() == name_of_sound.lower():
                return sound_entry
        return None

    def getSoundEntryByPath(self, path_to_sound):
        for sound_entry in self.key_bind_map.values():
            if sound_entry.path_to_sound == path_to_sound:
                return sound_entry
        return None

    def playSoundToFinish(self, sound_to_play):
        if not sound_to_play.is_playing: # if it not playing, start playing it
            thread.start_new_thread(sound_to_play.play, tuple())
        else: # if already playing, stop playing and restart the sound from the beginning
            thread.start_new_thread(sound_to_play.stop, tuple())
            counter = 0
            while sound_to_play.stream_in_use and counter < 1000: # wait for the sound_entry to finish outputting its current chunk to the stream if it is in the middle of doing so
                if counter > 100: print "stream is still in use after waiting 100ms... something is not right"
                time.sleep(.001)
                counter += 1
            thread.start_new_thread(sound_to_play.play, tuple())


    # def playSound(self, sound_to_play, last_sound_played=None, hold_to_play=False):
    #     if hold_to_play and last_sound_played is not None: # if hold to play is on and we just let go of the key for a sound
    #         thread.start_new_thread(last_sound_played.stop, tuple())
    #     else:
    #         if not sound_to_play.is_playing: # start playing it if it not playing
    #             thread.start_new_thread(sound_to_play.play, tuple())
    #         elif not hold_to_play: # stop playing it if hold_to_play is off and the key was let go
    #             thread.start_new_thread(sound_to_play.stop, tuple())
    #             counter = 0
    #             while sound_to_play.stream_in_use and counter < 1000: # wait for the sound_entry to finish outputting its current chunk to the stream if it is in the middle of doing so
    #                 if counter > 100: print "stream is still in use after waiting 100ms... something is not right"
    #                 time.sleep(.001)
    #                 counter += 1
    #             thread.start_new_thread(sound_to_play.play, tuple())




class SoundEntry:
    def __init__(self, path_to_sound, frames=None, activation_keys=frozenset(), is_playing=False, continue_playing=True, pitch_modifier=0):
        self.path_to_sound = path_to_sound
        self.activation_keys = activation_keys,
        self.frames = frames
        self.is_playing = is_playing
        self.continue_playing = continue_playing
        self.pitch_modifier = pitch_modifier
        self.p = pyaudio.PyAudio()
        self.stream_in_use = False

        self.mark_frame_index = False
        self.jump_to_marked_frame_index = True
        self.marked_frame_index = 0

        if self.frames is None and os.path.exists(self.path_to_sound):
            self.frames = Audio_Utils.getFramesFromFile(self.path_to_sound)
            self.frames = Audio_Utils.getNormalizedAudioFrames(self.frames, Audio_Utils.DEFAULT_DBFS)

        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=2,
            rate=44100,
            input=True,
            frames_per_buffer=1024,
            output=True,
            output_device_index=7
        )

        self.stream2 = self.p.open(
            format=pyaudio.paInt16,
            channels=2,
            rate=44100,
            input=True,
            frames_per_buffer=1024,
            output=True,
            output_device_index=5
        )


    def playMultiThreaded(self):
        print "playing", self.path_to_sound
        if not self.is_playing: # start playing it if it not playing
            thread.start_new_thread(self.play, tuple())
        else: # stop playing it if hold_to_play is off and the key was let go
            thread.start_new_thread(self.stop, tuple())
            counter = 0
            while self.stream_in_use and counter < 1000: # wait for the self to finish outputting its current chunk to the stream if it is in the middle of doing so
                time.sleep(.001)
                counter += 1
            thread.start_new_thread(self.play, tuple())


    def play(self, reset_frame_index=True):
        self.is_playing = True
        self.continue_playing = True

        if reset_frame_index:
            frame_index = 0
        else:
            frame_index = self.marked_frame_index

        while frame_index < len(self.frames) and self.continue_playing:
            if self.mark_frame_index:
                self.marked_frame_index = frame_index
                self.mark_frame_index = False
            elif self.jump_to_marked_frame_index:
                frame_index = self.marked_frame_index
                self.jump_to_marked_frame_index = False

            self.stream_in_use = True
            current_frame = self.frames[frame_index]
            current_frame = Audio_Utils.getPitchShiftedFrame(current_frame, self.pitch_modifier)
            self.stream.write(current_frame)
            self.stream2.write(current_frame)

            self.stream_in_use = False

            frame_index += 1

        self.is_playing = False


    def stop(self):
        self.continue_playing = False

    def moveMarkedFrameIndex(self, move_amount):
        self.marked_frame_index = max(0, self.marked_frame_index+Audio_Utils.secondsToFrames(move_amount)) # shift back in frames by .2 seconds. used max() with 0 to not get out of bounds error

    def markCurrentFrameIndex(self):
        self.mark_frame_index = True # in the loop of the self.Play() method, we check to see if this is true. if it is true, we mark the current frame index and then set this back to false

    def jumpToMarkedFrameIndex(self):
        self.jump_to_marked_frame_index = True
        if not self.is_playing:
            self.play()

    def shiftPitch(self, amount):
        self.pitch_modifier += amount

    def getSoundName(self):
        return os.path.basename(self.path_to_sound).replace(".wav", "")

    def __eq__(self, other):
        return type(self) == type(other) and self.path_to_sound == other.path_to_sound

    def __ne__(self, other):
        return not self.__eq__(other)


if __name__ == "__main__":
    sound = SoundEntry("x1.wav")
    sound.play()
