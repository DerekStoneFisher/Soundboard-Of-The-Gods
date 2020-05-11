import os
import threading
from SoundBoard_GUI import SoundBoardGUI
import pyHook
# from soundboard.audio.Recorder import AudioRecorder
from soundboard.entries.Sound_Library import SoundLibrary
from soundboard.audio.Pitch_Controller import PitchController

from soundboard.audio.Sound import SoundEntry, SoundCollection
from soundboard.keys.KeyPress import KeyPressManager
from soundboard.audio.recorder import RecordingManager
import thread
import pythoncom

PITCH_MODIFIERS = {'1':-.75, '2':-.6, '3':-.45, '4':-.3, '5':-.15, '6':0, '7':.15, '8':.3, '9':.45, '0':.6} # how much is the pitch shifted for each step in "piano-mode"
PITCH_SHIFT_AMOUNT = .1 # what multiplier is used to adjust the pitch with the left and right arrows
SHIFT_SECONDS = .1 # by how many seconds will the up and down arrows move the marked chunk index
SOUNDBOARD_JSON_FILE = "Board1.json"
SOUNDBOARD_SOUNDS_BASE_FOLDER_PATH = "C:/Users/Admin/Desktop/Soundboard"
SOUNDBOARD_RECORDINGS_PATH = "D:/Projects/Audio-Shadow-Play-Git/Audio_Backups"

GUI_ENABLED = True


class SoundBoardController:
    def __init__(self, soundCollection, keyPressManager, recorder):
        """
        Acts as the glue for soundCollection and keyPressManager.
        This class does not have an understanding of key-presses, only of sounds (except for _updateSoundboardConfiguration(), but I had to put that somewhere)
        :type soundCollection: SoundCollection
        :type keyPressManager: KeyPressManager
        :type recorder: RecordingManager
        """
        self.soundCollection = soundCollection
        self.keyPressManager = keyPressManager
        self.recorder = recorder
        self.hold_to_play = False
        self.pause_soundboard = False


    def runpyHookThread(self):
        hm = pyHook.HookManager()
        hm.KeyDown = self.handleKeyEvent
        hm.KeyUp = self.handleKeyEvent
        hm.HookKeyboard()
        if not GUI_ENABLED:
            try:
                pythoncom.PumpMessages() # ignore the "cant find reference" message here
            except KeyboardInterrupt:
                pass

    def handleKeyEvent(self, key_event):
        self.keyPressManager.processKeyEvent(key_event) # update data inside of keyPressManager about what key was pressed
        if self.keyPressManager.key_state_changed and not keyPressManager.last_event_was_key_release:
            self._updateSoundboardConfiguration() # use the now updated data stored inside of keyPressManager to update the configuration settings of the soundboard
            possible_new_sound_entry = self.soundCollection.getBestSoundEntryMatchOrNull(self.keyPressManager.getKeysDown())
            if not self.pause_soundboard and possible_new_sound_entry is not None:
                self.soundCollection.playSoundToFinish(possible_new_sound_entry)

        return True

    def getCurrentSoundEntry(self):
        return self.soundCollection.getCurrentSoundEntry()



    def _updateSoundboardConfiguration(self):
        sound = self.getCurrentSoundEntry()
        if keyPressManager.endingKeysEqual(["pause"]):
            self.pause_soundboard = not self.pause_soundboard
            self.soundCollection.stopAllSounds()
        elif self.pause_soundboard: # break early if soundboard is paused
            return


        elif self.keyPressManager.keysAreContainedInKeysDown(["1", "4"]):  # we use more lenient matching for this one
            thread.start_new_thread(sound.jumpToMarkedChunkIndex, tuple())  # need to call via a thread so we don't get blocked by the .play() which can get called by this function
        if self.keyPressManager.keysAreContainedInKeysDown(["tab", "4"]):  # we use more lenient matching for this one
            thread.start_new_thread(sound.jumpToSecondaryMarkedChunkIndex, tuple())  # need to call via a thread so we don't get blocked by the .play() which can get called by this function
        elif self.keyPressManager.keysAreContainedInKeysDown(["1", "7"]):
            thread.start_new_thread(sound.resumePlayingBeforeLastJump, tuple())  # need to call via a thread so we don't get blocked by the .play() which can get called by this function


        if len(self.keyPressManager.getKeysDown()) >= 2 and self.keyPressManager.getKeysDown()[0] == "menu" and self.keyPressManager.getKeysDown()[-1] in PITCH_MODIFIERS:
            sound.pitch_modifier = PITCH_MODIFIERS[self.keyPressManager.getKeysDown()[-1]]
            thread.start_new_thread(sound.jumpToMarkedChunkIndex, tuple()) # need to call via a thread so we don't get blocked by the .play() which can get called by this function

       # key binds that affect all sounds in the sound collection
        elif keyPressManager.endingKeysEqual(["tab", "return"]): # tab + enter -> clear non-playing sounds from the "recent sounds queue"
            print "self.clearAllNonPlayingSoundsFromTheFrontOfPreviousSoundsQueue()"
            self.soundCollection.previous_sounds.clearAllNonPlayingSoundsFromTheFrontOfPreviousSoundsQueue()
        elif self.keyPressManager.endingKeysEqual(["return"]): # enter -> stop all currently playing sounds
            self.soundCollection.stopAllSounds()
        elif self.keyPressManager.endingKeysEqual(["tab", "left", "right"]): # left + right -> reset pitch of all sounds
            self.soundCollection.resetAllPitches()
        elif keyPressManager.endingKeysEqual(["menu", "x"]):
            self.recorder.toggleRecord()
        elif keyPressManager.endingKeysEqual(["tab", "left"]):
            self.recorder.loadPreviousRecording()
        elif keyPressManager.endingKeysEqual(["tab", "right"]):
            self.recorder.loadNextRecording()
        elif keyPressManager.endingKeysEqual(["tab", "delete"]):
            self.recorder.deleteCurrentRecording()
        elif keyPressManager.endingKeysEqual(["tab", "/"]):
            self.recorder.renameCurrentRecording()
        elif keyPressManager.endingKeysEqual(["tab", "oem_comma"]):
            self.recorder.recorder.moveRecordingStartBack(.5)
            self.recorder.refreshRecording()
            self.soundCollection.playSoundToFinish(soundCollection.getSoundEntryByName('x.wav'))
        elif keyPressManager.endingKeysEqual(["tab", "oem_period"]):
            self.recorder.recorder.moveRecordingStartForward(.5)
            self.recorder.refreshRecording()
            self.soundCollection.playSoundToFinish(soundCollection.getSoundEntryByName('x.wav'))
        elif self.keyPressManager.endingKeysEqual(["menu", "left"]): # alt + left -> shift down pitch of currently playing sound
            self.soundCollection.shiftAllPitches(-PITCH_SHIFT_AMOUNT)
        elif self.keyPressManager.endingKeysEqual(["menu", "right"]): # alt + right (insert trump joke here xd) -> shift down pitch of currently playing sound
            self.soundCollection.shiftAllPitches(PITCH_SHIFT_AMOUNT)
        elif self.keyPressManager.endingKeysEqual(["left"]): # left (without alt) -> shift down pitch of all sounds
            sound.shiftPitch(-PITCH_SHIFT_AMOUNT)
        elif self.keyPressManager.endingKeysEqual(["right"]): # right (without alt) -> shift up pitch of all sounds
            sound.shiftPitch(PITCH_SHIFT_AMOUNT)


        # key binds that affect the last sound played
        elif self.keyPressManager.endingKeysEqual(["tab", "down"]):
            sound.activateGradualPitchShift(-1)
        elif self.keyPressManager.endingKeysEqual(["tab", "up"]):
            sound.activateGradualPitchShift(1)

        # OSCILLATE
        elif self.keyPressManager.endingKeysEqual(["tab","\\"]) or self.keyPressManager.endingKeysEqual(["tab", "2"]):
            sound.activateOscillate()
        elif self.keyPressManager.endingKeysEqual(["tab", "["]):
            PitchController.adjustOscillationRate(-1)
            sound.oscillation_chunks_remaining = 690
        elif self.keyPressManager.endingKeysEqual(["tab", "]"]):
            PitchController.adjustOscillationRate(1)
            sound.oscillation_chunks_remaining = 690
        elif self.keyPressManager.endingKeysEqual(["tab", "o"]):
            PitchController.adjustOscillationAmplitude(-1)
            sound.oscillation_chunks_remaining = 690
        elif self.keyPressManager.endingKeysEqual(["tab", "p"]):
            PitchController.adjustOscillationAmplitude(1)
            sound.oscillation_chunks_remaining = 690

        # WOBBLE
        elif self.keyPressManager.endingKeysEqual(["tab", "5"]):
            sound.activateWobble()
            sound.wobble_chunks_remaining = 690
        elif self.keyPressManager.endingKeysEqual(["tab", ";"]):
            PitchController.adjustWobblePauseFrequency(-1)
            sound.wobble_chunks_remaining = 690
        elif self.keyPressManager.endingKeysEqual(["tab", "'"]):
            PitchController.adjustWobblePauseFrequency(1)
            sound.wobble_chunks_remaining = 690
        elif self.keyPressManager.endingKeysEqual(["tab", "k"]):
            PitchController.adjustWobbleAmplitude(-1)
            sound.wobble_chunks_remaining = 690
        elif self.keyPressManager.endingKeysEqual(["tab", "l"]):
            PitchController.adjustWobbleAmplitude(1)
            sound.wobble_chunks_remaining = 690

        elif self.keyPressManager.endingKeysEqual(["up"]):
            sound.moveMarkedChunkIndex(SHIFT_SECONDS)
        elif self.keyPressManager.endingKeysEqual(["down"]):
            sound.moveMarkedChunkIndex(-SHIFT_SECONDS)
        elif self.keyPressManager.endingKeysEqual(["1","3"]):
            sound.markCurrentChunkIndex()
        elif self.keyPressManager.endingKeysEqual(["tab", "3"]):
            sound.markSecondaryChunkIndex()
        elif self.keyPressManager.endingKeysEqual(["1", "2"]):
            self.soundCollection.previous_sounds.swapCurrentAndPreviousSoundEntry()
        elif self.keyPressManager.endingKeysEqual(["`"]):
             sound.stop() # no new thread needed
        elif self.keyPressManager.endingKeysEqual(["1", "6"]) :
            self.soundCollection.playSoundToFinish(sound)
        elif self.keyPressManager.endingKeysEqual(["1", "5"]):
            if sound.is_playing:
                sound.markCurrentChunkIndex()
                sound.stop()
            else:
                sound.reset_chunk_index_on_play = False
                self.soundCollection.playSoundToFinish(sound)
        elif self.keyPressManager.endingKeysEqual(["2", "5"]):
            if not sound.is_playing:
                self.soundCollection.playSoundToFinish(sound)
            else:
                sound.reverse_mode = not sound.reverse_mode
        elif self.keyPressManager.endingKeysEqual(["tab", "1"]): # stop current sound, swap to last sound and start playing
            self.soundCollection.previous_sounds.stopCurrentSwapToPreviousAndStartPlaying()
        # elif self.keyPressManager.endingKeysEqual(["tab", "6"]):
        #     sound.matchBpmWithAnotherSound(self.getPreviousSoundEntry())
        # elif self.keyPressManager.endingKeysEqual(["tab", "7"]):
        #     sound.autoDetectBpm()
        # elif self.keyPressManager.endingKeysEqual(["tab", "q"]):
        #     sound.bpm_obj.update()
        #     print sound.bpm_obj.avg_bpm
        # elif self.keyPressManager.endingKeysEqual(["tab", "w"]):
        #     sound.bpm = sound.bpm_obj.avg_bpm
        # elif self.keyPressManager.endingKeysEqual(["tab", "e"]):
        #     sound.bpm_obj.restart()




if __name__ == "__main__":
    soundLibrary = SoundLibrary(SOUNDBOARD_JSON_FILE, SOUNDBOARD_SOUNDS_BASE_FOLDER_PATH)
    soundCollection = SoundCollection(soundLibrary)
    for key_bind in soundCollection.key_bind_map:
        print list(key_bind), os.path.basename(soundCollection.key_bind_map[key_bind].path_to_sound)

    keyPressManager = KeyPressManager()

    audioRecorder = RecordingManager(SOUNDBOARD_RECORDINGS_PATH, soundCollection.getSoundEntryByName('x.wav'))
    soundboardController = SoundBoardController(soundCollection, keyPressManager, audioRecorder)
    if not GUI_ENABLED:
        pyHook_t = threading.Thread(target=soundboardController.runpyHookThread)
        pyHook_t.start()
    else:
        soundBoardGUI = SoundBoardGUI(soundCollection, keyPressManager, audioRecorder, soundboardController, soundLibrary)
        soundBoardGUI.root.after(1000, soundboardController.runpyHookThread)
        soundBoardGUI.runGUI()




