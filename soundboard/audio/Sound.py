from collections import OrderedDict
import Audio_Utils
import pyaudio
import BPM_Utils
import os
import time, thread

from soundboard.audio.stream import SharedStreamManager
from soundboard.audio.Pitch_Controller import PitchController

SOUND_QUEUE_MAX_SIZE = 5

class PreviousSounds:
    def __init__(self):
        self.previous_sounds_queue = []

    def updateQueueWithNewSoundEntry(self, sound_entry_to_add):
        if self.getCurrentSoundEntry() != sound_entry_to_add and sound_entry_to_add is not None:
            if len(self.previous_sounds_queue) >= SOUND_QUEUE_MAX_SIZE:
                del(self.previous_sounds_queue[0])
            self.previous_sounds_queue.append(sound_entry_to_add)

    def getCurrentSoundEntry(self):
        """
        :rtype: SoundEntry
        """
        return self.previous_sounds_queue[-1]

    def getPreviousSoundEntry(self):
        """
        :rtype: SoundEntry
        """
        return self.previous_sounds_queue[-2]

    def swapCurrentAndPreviousSoundEntry(self):
        print "'", self.previous_sounds_queue[-1].getSoundName()  + "' -> '" + self.previous_sounds_queue[-2].getSoundName() + "'"
        self.previous_sounds_queue[-1], self.previous_sounds_queue[-2] = self.previous_sounds_queue[-2], self.previous_sounds_queue[-1]

    def clearAllNonPlayingSoundsFromTheFrontOfPreviousSoundsQueue(self):
        last_playing_sound_index = 0
        for i in range(0, len(self.previous_sounds_queue)):
            if self.previous_sounds_queue[i].is_playing:
                last_playing_sound_index = i
        self.previous_sounds_queue = self.previous_sounds_queue[0:last_playing_sound_index+1]

    def stopCurrentSwapToPreviousAndStartPlaying(self):
        self.getCurrentSoundEntry().stop()
        self.swapCurrentAndPreviousSoundEntry()
        self.getCurrentSoundEntry().reset_chunk_index_on_play = False
        thread.start_new_thread(self.getCurrentSoundEntry().play, tuple())



class SoundCollection:
    def __init__(self, sound_library):
        '''
        Acts as a storage container and manager for all the SoundEntry instances
        Can globally shift all pitches, find the best matching sound entry given a string, or stop all sounds
        :param sound_library: SoundLibrary
        '''

        self.key_bind_map = OrderedDict()
        self.sound_entry_path_map = OrderedDict()
        self.previous_sounds = PreviousSounds()


        for activation_keys, sound_path in sound_library.getKeyBindMap().items():
            sound_entry = SoundEntry(sound_path, activation_keys=activation_keys)
            self.addSoundEntry(sound_entry)

        # give previous sounds queue 2 random sounds to start with
        self.previous_sounds.previous_sounds_queue += [next(iter(self.key_bind_map.values())),
          next(iter(self.key_bind_map.values()))]

    def getCurrentSoundEntry(self):
        return self.previous_sounds.getCurrentSoundEntry()

    def addSoundEntry(self, sound_entry):
        self.sound_entry_path_map[sound_entry.path_to_sound] = sound_entry
        self.key_bind_map[sound_entry.activation_keys] = sound_entry

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
        self.previous_sounds.updateQueueWithNewSoundEntry(sound_to_play)
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
    def __init__(self, path_to_sound, chunks=None, activation_keys=frozenset()):
        """
        :type path_to_sound: str
        :type chunks: list
        :type pitch_modifier: float
        """
        self.path_to_sound = path_to_sound
        # print "initializing sound:", os.path.basename(path_to_sound), "with key bind:", ", ".join(activation_keys)
        self.activation_keys = activation_keys
        self.chunks = chunks
        self.reverse_chunks = chunks
        self.is_playing = False
        self.pitch_modifier = 0
        self.p = pyaudio.PyAudio()
        self.stream_in_use = False

        self.chunk_index = 0
        self.reset_chunk_index_on_play = True

        self.jump_to_marked_chunk_index = False
        self.marked_chunk_index = 0

        self.jump_to_secondary_chunk_index = False
        self.secondary_marked_chunk_index = 0

        self.gradual_pitch_shift_direction = 1
        self.gradual_pitch_shift_chunks_remaining = 0

        self.oscillation_chunks_remaining = 0
        self.oscillation_generator = None
        self.oscillation_pitch = 0 # how much above or below 0 our pitch has changed due to oscillation

        self.wobble_chunks_remaining = 0
        self.wobble_generator = None
        self.wobble_pitch = 0

        self.current_sharedStream = None
        self.shared_steam_index = None

        self.reverse_mode = False

        # when set to true, skip to the position saved right before a "jump to marked chunk index" jump was done
        self.have_jumped = False
        self.undo_marked_chunk_jump = False
        self.index_before_jump = 0

        # self.bpm = None
        # self.bpm_obj = BPM_Utils.BPM()

        # self.time_stretch_enabled = False
        # self.time_stretch_rate = 1
        # self.AUDIO_UNITS_PER_CHUNK = (1024 / 2) / 2 # 1024 bytes per chunk, 2 bytes for 1 16bit int, 2 channels = 1024/2/2 "audio units" per chunk
        # self.time_stretched_audio_unit_buffer = []


        if self.chunks is None and os.path.exists(self.path_to_sound):
            self.reloadChunksFromFile()
        else:
            self.chunks = None
            self.speaker_stream = None
            self.virtual_speaker_stream = None

    def play(self):
        if self.chunks is None:
            raise ValueError("Error: cannot play sound self.chunks == None. The sound file was most likely deleted. sound = " + self.path_to_sound)

        if self.current_sharedStream is None:
            self.current_sharedStream, self.shared_steam_index = SharedStreamManager.getUnusedStreamAndIndex()
        if self.chunks is None and os.path.exists(self.path_to_sound):
            self.reloadChunksFromFile()

        self.is_playing = True

        if self.reset_chunk_index_on_play:
            self.chunk_index = 0
        else:
            self.chunk_index = self.marked_chunk_index
            self.reset_chunk_index_on_play = True # auto switch back after one play

        while self.chunk_index < len(self.chunks) and self.is_playing:
            if self.jump_to_marked_chunk_index:
                self.chunk_index = self.marked_chunk_index
                self.jump_to_marked_chunk_index = False
            elif self.jump_to_secondary_chunk_index:
                self.chunk_index = self.secondary_marked_chunk_index
                self.jump_to_secondary_chunk_index = False
            elif self.undo_marked_chunk_jump:
                self.chunk_index = self.index_before_jump + (self.chunk_index - self.marked_chunk_index)
                self.undo_marked_chunk_jump = False

            current_chunk = self.chunks[min(self.chunk_index, len(self.chunks)-1)]

            # OSCILLATION DONE HERE
            if self.oscillation_chunks_remaining > 0:
                print self.oscillation_chunks_remaining, self.oscillation_pitch, self.pitch_modifier
                pitch_change = next(self.oscillation_generator)
                self.pitch_modifier += pitch_change
                self.oscillation_pitch += pitch_change
                self.oscillation_chunks_remaining -= 1

                # if oscillation finished before it could return back to the pitch from where it started,
                # then mark it as not finished and let it try again next time
                if self.oscillation_chunks_remaining == 0 and abs(self.oscillation_pitch) > 0.0001:
                    if abs(self.oscillation_pitch) > abs(PitchController.oscillation_rate):
                        self.oscillation_chunks_remaining = 1
                    else:
                        self.pitch_modifier -= self.oscillation_pitch
                        self.oscillation_pitch = 0

            # WOBBLE DONE HERE
            if self.wobble_chunks_remaining > 0:
                pitch_change = next(self.wobble_generator)
                self.pitch_modifier += pitch_change
                self.wobble_pitch += pitch_change
                self.wobble_chunks_remaining -= 1

                if self.wobble_chunks_remaining == 0:
                    self.pitch_modifier -= self.wobble_pitch
                    self.wobble_pitch = 0

            # SLO-MO/SPEED-UP DONE HERE
            if self.gradual_pitch_shift_chunks_remaining> 0:
                self.pitch_modifier += PitchController.gradual_pitch_shift_rate * self.gradual_pitch_shift_direction
                self.gradual_pitch_shift_chunks_remaining -= 1

            # round the pitch modifier to 0 if its close enough, I want zero comparison to work
            if -0.0001 < float(self.pitch_modifier) < 0.0001:
                self.pitch_modifier = 0

            if self.pitch_modifier != 0:
                current_chunk = Audio_Utils.getPitchShiftedChunk(current_chunk, self.pitch_modifier)

            self._writeChunkToStreams(current_chunk)

            if self.reverse_mode:
                self.chunk_index = max(0, self.chunk_index-1) # prevent out of bounds
                if self.chunk_index == 0:
                    self.reverse_mode = False
                    self.stop()
                    self.reset_chunk_index_on_play = False
            else:
                self.chunk_index += 1

        self.is_playing = False
        SharedStreamManager.releaseStreamAtIndex(self.shared_steam_index)
        self.current_sharedStream = None

    def _writeChunkToStreams(self, chunk):
        self.stream_in_use = True
        # if self.time_stretch_enabled:
        #     self._handleTimeStretchWriteChunkToStreams(chunk)
        if self.reverse_mode:
            self.current_sharedStream.playChunk(Audio_Utils.getReversedChunk(chunk))
        else:
            self.current_sharedStream.playChunk(chunk)
        self.stream_in_use = False

    def stop(self):
        self.is_playing = False

    def moveMarkedChunkIndex(self, move_amount):
        self.marked_chunk_index = max(0, self.marked_chunk_index+Audio_Utils.secondsToChunks(move_amount)) # shift back in chunks by .2 seconds. used max() with 0 to not get out of bounds error

    def markCurrentChunkIndex(self):
        self.marked_chunk_index = max(0, self.chunk_index-5)

    def markSecondaryChunkIndex(self):
        self.secondary_marked_chunk_index = max(0, self.chunk_index-5)

    def jumpToMarkedChunkIndex(self):
        if not self.have_jumped: # if we jump multiple times in a row, don't overwrite our saved position before the jump
            self.index_before_jump = self.chunk_index
            self.have_jumped = True

        self.jump_to_marked_chunk_index = True
        if not self.is_playing:
            self.play()

    def jumpToSecondaryMarkedChunkIndex(self):
        self.jump_to_secondary_chunk_index = True
        if not self.is_playing:
            self.play()

    def resumePlayingBeforeLastJump(self):
        if self.have_jumped:
            self.undo_marked_chunk_jump = True
            self.have_jumped = False
            if not self.is_playing:
                self.play()

    def shiftPitch(self, amount):
        print "pitch", self.pitch_modifier, " -> ", self.pitch_modifier+amount
        self.pitch_modifier += amount

    def activateOscillate(self):
        self.oscillation_chunks_remaining = Audio_Utils.secondsToChunks(1)
        if self.oscillation_generator is None:
            self.oscillation_generator = PitchController.genOscillate()

    def activateWobble(self):
        self.wobble_chunks_remaining = Audio_Utils.secondsToChunks(1)
        if self.wobble_generator is None:
            self.wobble_generator = PitchController.genWobble()

    def activateGradualPitchShift(self, direction):
        self.gradual_pitch_shift_direction = direction
        self.gradual_pitch_shift_chunks_remaining = Audio_Utils.secondsToChunks(.6)


    def getSoundName(self):
        return os.path.basename(self.path_to_sound).replace(".wav", "")

    def reloadChunksFromFile(self):
        self.chunks = Audio_Utils.getChunksFromFile(self.path_to_sound)
        self.chunks = Audio_Utils.getChunksWithoutStartingSilence(self.chunks)
        self.chunks = Audio_Utils.getNormalizedAudioChunks(self.chunks, Audio_Utils.DEFAULT_DBFS)
        # self.chunks = Audio_Utils.getReversedChunks(self.chunks)




    def getLengthOfSoundInSeconds(self):
        return Audio_Utils.chunksToSeconds(len(self.chunks))


    # def autoDetectBpm(self):
    #     self.bpm = BPM_Utils.getBpmFromWavFile(self.path_to_sound)
    #     print self.getSoundName() + " has bpm " + str(self.bpm)
    #
    # def matchBpmWithAnotherSound(self, anotherSound):
    #     """
    #     :type anotherSound: SoundEntry
    #     """
    #     if self.bpm is None:
    #         self.autoDetectBpm()
    #     if anotherSound.bpm is None:
    #         anotherSound.autoDetectBpm()
    #     self.pitch_modifier = 1 - (self.bpm / anotherSound.bpm)
    #     print "setting pitch modifier of " + self.getSoundName() + " to " + str(self.pitch_modifier) + " to match bpm of " + anotherSound.getSoundName() + ". bpm changed from " + str(self.bpm) + " -> " + str(self.bpm)


    def __eq__(self, other):
        return type(self) == type(other) and self.path_to_sound == other.path_to_sound

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.path_to_sound)