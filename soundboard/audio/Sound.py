from collections import OrderedDict
import Audio_Utils
import pyaudio
import BPM_Utils
import os
import time, thread

from soundboard.audio.stream import SharedStreamManager
from random import randrange



class SoundCollection:
    def __init__(self, sound_library):
        '''
        Acts as a storage container and manager for all the SoundEntry instances
        Can globally shift all pitches, find the best matching sound entry given a string, or stop all sounds
        :param sound_library: SoundLibrary
        '''

        self.key_bind_map = OrderedDict()
        self.sound_entry_path_map = OrderedDict()

        for activation_keys, sound_path in sound_library.getKeyBindMap().items():
            sound_entry = SoundEntry(sound_path, activation_keys=activation_keys)
            self.addSoundEntry(sound_entry)

    def addSoundEntry(self, soundEntry):
        self.sound_entry_path_map[soundEntry.path_to_sound] = soundEntry
        self.key_bind_map[soundEntry.activation_keys] = soundEntry

    def createAndAddSoundEntry(self, path_to_sound, activation_keys):
        if type(activation_keys) == type(list()):
            activation_keys = frozenset(activation_keys)
        self.addSoundEntry(SoundEntry(path_to_sound, activation_keys=activation_keys))

    def stopAllSounds(self):
        for soundEntry in self.sound_entry_path_map.values():
            soundEntry.stop()

    def resetAllPitches(self):
        for soundEntry in self.sound_entry_path_map.values():
            soundEntry.pitch_modifier = 0

    def shiftAllPitches(self, shift_amount):
        for soundEntry in self.sound_entry_path_map.values():
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
                if keys_down[0] in ['tab', 'menu']: # a special command like "Tab + [" shouldn't trigger the "[" sound effect
                     return None
                del(keys_down[0])
        return None

    def getSoundEntryByName(self, name_of_sound):
        for sound_entry in self.sound_entry_path_map.values():
            if os.path.basename(sound_entry.path_to_sound).lower() == name_of_sound.lower():
                return sound_entry
        return None

    def getSoundEntryByPath(self, path_to_sound):
        for sound_entry in self.sound_entry_path_map.values():
            if sound_entry.path_to_sound == path_to_sound:
                return sound_entry
        return None

    def playSoundToFinish(self, sound_to_play):
        print "playing '" + sound_to_play.getSoundName() + "'"
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




class SoundEntry:
    def __init__(self, path_to_sound, frames=None, activation_keys=frozenset(), is_playing=False, continue_playing=True, pitch_modifier=0, wait_to_load_sound=True):
        """
        :type path_to_sound: str
        :type frames: list
        :type pitch_modifier: float
        """
        self.path_to_sound = path_to_sound
        # print "initializing sound:", os.path.basename(path_to_sound), "with key bind:", ", ".join(activation_keys)
        self.activation_keys = activation_keys
        self.frames = frames
        self.reverse_frames = frames
        self.is_playing = is_playing
        self.continue_playing = continue_playing
        self.pitch_modifier = pitch_modifier
        self.wait_to_load_sound = wait_to_load_sound
        self.p = pyaudio.PyAudio()
        self.stream_in_use = False

        self.frame_index = 0
        self.reset_frame_index_on_play = True

        self.jump_to_marked_frame_index = False
        self.marked_frame_index = 0

        self.jump_to_secondary_frame_index = False
        self.secondary_marked_frame_index = 0

        self.slow_motion_slow_rate = .01 # how much each frame is slowed down or sped up by when we activate slow mo or speed up
        # self.slow_motion_slow_frames = 80 # over the course of how many frames will we slow down or speed up when activating
        self.slow_motion_started = False # when this is set to true, start slowing doing for "slow_motion_frames_left" frames
        self.slow_motion_frames_left = 0 # number of frames to continue slowing down for
        self.speed_up_started = False # signal to start speeding up  for "speed_up_to_normal" frames left
        self.speed_up_frames_left = 0 # number of frames to continue speeding up for

        self.oscillation_rate = .1 # .03 # cycles between negative and positive during oscillation
        self.oscillation_amplitude = 1
        self.oscillation_frames_remaining = 0
        self.oscillation_generator = None
        self.oscillation_pause_frequency = 0

        self.current_sharedStream = None
        self.shared_steam_index = None

        self.reverse_mode = False

        # when set to true, skip to the position saved right before a "jump to marked frame index" jump was done
        self.have_jumped = False
        self.undo_marked_frame_jump = False
        self.index_before_jump = 0

        self.bpm = None
        self.bpm_obj = BPM_Utils.BPM()

        self.time_stretch_enabled = False
        self.time_stretch_rate = 1
        self.AUDIO_UNITS_PER_FRAME = (1024 / 2) / 2 # 1024 bytes per frame, 2 bytes for 1 16bit int, 2 channels = 1024/2/2 "audio units" per frame
        self.time_stretched_audio_unit_buffer = []


        if self.frames is None and os.path.exists(self.path_to_sound):
            self.reloadFramesFromFile()
        else:
            self.frames = None
            self.speaker_stream = None
            self.virtual_speaker_stream = None

    def play(self):
        if self.frames is None:
            raise ValueError("Error: cannot play sound self.frames == None. The sound file was most likely deleted. sound = " + self.path_to_sound)

        if self.current_sharedStream is None:
            self.current_sharedStream, self.shared_steam_index = SharedStreamManager.getUnusedStreamAndIndex()
        if self.frames is None and os.path.exists(self.path_to_sound):
            self.reloadFramesFromFile()

        self.is_playing = True
        self.continue_playing = True

        if self.reset_frame_index_on_play:
            self.frame_index = 0
        else:
            self.frame_index = self.marked_frame_index
            self.reset_frame_index_on_play = True # auto switch back after one play


        while self.frame_index < len(self.frames) and self.continue_playing:
            if self.jump_to_marked_frame_index:
                self.frame_index = self.marked_frame_index
                self.jump_to_marked_frame_index = False
            elif self.jump_to_secondary_frame_index:
                self.frame_index = self.secondary_marked_frame_index
                self.jump_to_secondary_frame_index = False
            elif self.undo_marked_frame_jump:
                self.frame_index = self.index_before_jump + (self.frame_index - self.marked_frame_index)
                self.undo_marked_frame_jump = False

            current_frame = self.frames[min(self.frame_index, len(self.frames)-1)]

            if self.oscillation_frames_remaining > 0:
                next(self.oscillation_generator)

            # do slow motion stuff here
            if self.slow_motion_started:
                if self.slow_motion_frames_left > 0:
                    self.slow_motion_frames_left -= 1
                    #if frame_index % self.slow_motion_frame_skip_rate == 0:
                    self.pitch_modifier -= self.slow_motion_slow_rate
                else:
                    self.slow_motion_started = False
            elif self.speed_up_started:
                if self.speed_up_frames_left > 0:
                    self.speed_up_frames_left -= 1
                    #if frame_index % self.slow_motion_frame_skip_rate == 0:
                    self.pitch_modifier += self.slow_motion_slow_rate
                else:
                    self.speed_up_started = False


            # round the pitch modifier to 0 if its close enough, I want zero comparison to work
            if -0.0001 < float(self.pitch_modifier) < 0.0001:
                self.pitch_modifier = 0

            if self.pitch_modifier != 0:
                current_frame = Audio_Utils.getPitchShiftedFrame(current_frame, self.pitch_modifier)
                # if self.frame_index % 100 == 0:
                #     print "current pitch is ", self.pitch_modifier
                #     print "oscillation shift is", self.oscillate_shift, "frames between oscillation shifts", self.frames_between_oscillate_shifts, "half_oscillation_cycles_remaining", self.half_oscillation_cycles_remaining


            self._writeFrameToStreams(current_frame)

            if self.reverse_mode:
                self.frame_index = max(0, self.frame_index-1) # prevent out of bounds
                if self.frame_index == 0:
                    self.reverse_mode = False
                    self.stop()
                    self.reset_frame_index_on_play = False
            else:
                self.frame_index += 1

        self.is_playing = False
        SharedStreamManager.releaseStreamAtIndex(self.shared_steam_index)
        self.current_sharedStream = None

    def _writeFrameToStreams(self, frame):
        self.stream_in_use = True
        if self.time_stretch_enabled:
            self._handleTimeStretchWriteFrameToStreams(frame)
        elif self.reverse_mode:
            self.current_sharedStream.playFrame(Audio_Utils.getReversedFrame(frame))
        else:
            self.current_sharedStream.playFrame(frame)
        self.stream_in_use = False

    def _handleTimeStretchWriteFrameToStreams(self, frame):
        atomic_audio_units = Audio_Utils.unpackFrameIntoAtomicAudioUnits(frame)
        atomic_audio_units = [x for i, x in enumerate(atomic_audio_units) if i % (1-self.pitch_modifier)*10 != 0]


        print "atomic audio units size is " + str(len(atomic_audio_units)) + " and modulo is " + str((1-self.pitch_modifier)*10)
        self.time_stretched_audio_unit_buffer.extend(atomic_audio_units)
        # if buffer exactly full after adding stretched frame contents, play it and empty it
        if len(self.time_stretched_audio_unit_buffer) == self.AUDIO_UNITS_PER_FRAME:
            self.current_sharedStream.playFrame(Audio_Utils.buildFrameFromAtomicAudioUnits(self.time_stretched_audio_unit_buffer))
            print str.format("exactly filled buffer {}", len(self.time_stretched_audio_unit_buffer))

            self.time_stretched_audio_unit_buffer = []
        # if buffer not yet full after adding stretched frame contents, do nothing
        elif len(self.time_stretched_audio_unit_buffer) < self.AUDIO_UNITS_PER_FRAME:
            print str.format("buffer not yet full. only size {}", len(self.time_stretched_audio_unit_buffer))
        # if buffer overly-full after adding stretched frame contents, play the first non-overfilled part and save the overfilled part as the new buffer
        elif len(self.time_stretched_audio_unit_buffer) > self.AUDIO_UNITS_PER_FRAME:
            first_audio_units = self.time_stretched_audio_unit_buffer[0:self.AUDIO_UNITS_PER_FRAME]
            remaining_audio_units = self.time_stretched_audio_unit_buffer[self.AUDIO_UNITS_PER_FRAME:]
            self.current_sharedStream.playFrame(Audio_Utils.buildFrameFromAtomicAudioUnits(first_audio_units))
            print str.format("filled buffer {} and remaining part {}", len(first_audio_units), len(remaining_audio_units))
            self.time_stretched_audio_unit_buffer = remaining_audio_units

    def stop(self):
        self.continue_playing = False

    def moveMarkedFrameIndex(self, move_amount):
        self.marked_frame_index = max(0, self.marked_frame_index+Audio_Utils.secondsToFrames(move_amount)) # shift back in frames by .2 seconds. used max() with 0 to not get out of bounds error

    def markCurrentFrameIndex(self):
        self.marked_frame_index = max(0, self.frame_index-5)

    def markSecondaryFrameIndex(self):
        self.secondary_marked_frame_index = max(0, self.frame_index-5)

    def jumpToMarkedFrameIndex(self):
        if not self.have_jumped: # if we jump multiple times in a row, don't overwrite our saved position before the jump
            self.index_before_jump = self.frame_index
            self.have_jumped = True

        self.jump_to_marked_frame_index = True
        if not self.is_playing:
            self.play()

    def jumpToSecondaryMarkedFrameIndex(self):
        self.jump_to_secondary_frame_index = True
        if not self.is_playing:
            self.play()

    def resumePlayingBeforeLastJump(self):
        if self.have_jumped:
            self.undo_marked_frame_jump = True
            self.have_jumped = False
            if not self.is_playing:
                self.play()

    def shiftPitch(self, amount):
        print "pitch", self.pitch_modifier, " -> ", self.pitch_modifier+amount
        self.pitch_modifier += amount

    def activateSlowMotion(self):
        self.slow_motion_frames_left = 80
        self.slow_motion_started = True

    def activateSpeedUpMotion(self):
        self.speed_up_frames_left = 80
        self.speed_up_started = True

    def activateOscillate(self):
        self.oscillation_frames_remaining = 240
        if self.oscillation_generator is None:
            self.oscillation_generator = self.oscillate()


    def oscillate(self):
        """
        """
        print('first call')
        direction = 1.0 # switch to -1 when we hit the peak
        curr_wave_height = 0.0
        print curr_wave_height
        pauses_left = self.oscillation_pause_frequency

        while self.oscillation_frames_remaining > 0:
            while pauses_left > 0:
                pauses_left -= 1
                yield
            if self.oscillation_pause_frequency > 0:
                pauses_left = randrange(0, self.oscillation_pause_frequency)

            if direction == 1 and curr_wave_height >= self.oscillation_amplitude/2:
                direction = -1
            elif direction == -1 and curr_wave_height <= -self.oscillation_amplitude/2:
                direction = 1

            # separately add to both
            curr_wave_height += (self.oscillation_rate * direction)
            self.pitch_modifier += (self.oscillation_rate * direction)

            self.oscillation_frames_remaining -= 1

            if self.oscillation_frames_remaining == 0 and abs(curr_wave_height) > 0.0001:
                print "0 frames left but curr_wave_height is", curr_wave_height, "so setting frames left to", curr_wave_height / self.oscillation_rate
                self.oscillation_frames_remaining = abs(curr_wave_height // self.oscillation_rate)
                # if abs(self.pitch_modifier) > 0.0001:
                #     print "last iteration, self.pitch_modifier", self.pitch_modifier, "-= curr_wave_height", curr_wave_height
                #     self.pitch_modifier -= curr_wave_height
            print curr_wave_height
            yield


    def getSoundName(self):
        return os.path.basename(self.path_to_sound).replace(".wav", "")

    def reloadFramesFromFile(self):
        self.frames = Audio_Utils.getFramesFromFile(self.path_to_sound)
        self.frames = Audio_Utils.getFramesWithoutStartingSilence(self.frames)
        self.frames = Audio_Utils.getNormalizedAudioFrames(self.frames, Audio_Utils.DEFAULT_DBFS)
        # self.frames = Audio_Utils.getReversedFrames(self.frames)




    def getLengthOfSoundInSeconds(self):
        return Audio_Utils.framesToSeconds(len(self.frames))


    def autoDetectBpm(self):
        self.bpm = BPM_Utils.getBpmFromWavFile(self.path_to_sound)
        print self.getSoundName() + " has bpm " + str(self.bpm)

    def matchBpmWithAnotherSound(self, anotherSound):
        """
        :type anotherSound: SoundEntry
        """
        if self.bpm is None:
            self.autoDetectBpm()
        if anotherSound.bpm is None:
            anotherSound.autoDetectBpm()
        self.pitch_modifier = 1 - (self.bpm / anotherSound.bpm)
        print "setting pitch modifier of " + self.getSoundName() + " to " + str(self.pitch_modifier) + " to match bpm of " + anotherSound.getSoundName() + ". bpm changed from " + str(self.bpm) + " -> " + str(self.bpm)


    def __eq__(self, other):
        return type(self) == type(other) and self.path_to_sound == other.path_to_sound

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.path_to_sound)