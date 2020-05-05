import os
from SoundBoard_GUI import SoundBoardGUI
import pyHook
from Recorder import AudioRecorder
from Sound_Library import SoundLibrary
from Pitch_Controller import PitchController

from Sound import SoundEntry, SoundCollection
from KeyPress import KeyPressManager
import thread

SOUND_QUEUE_MAX_SIZE = 5
PITCH_MODIFIERS = {'1':-.75, '2':-.6, '3':-.45, '4':-.3, '5':-.15, '6':0, '7':.15, '8':.3, '9':.45, '0':.6} # how much is the pitch shifted for each step in "piano-mode"
PITCH_SHIFT_AMOUNT = .1 # what multiplier is used to adjust the pitch with the left and right arrows
SHIFT_SECONDS = .1 # by how many seconds will the up and down arrows move the marked frame index
SOUNDBOARD_JSON_FILE = "Board1.json"
SOUNDBOARD_SOUNDS_BASE_FOLDER_PATH = "C:/Users/Admin/Desktop/Soundboard"


class SoundBoardController:
    """
    Acts as the glue for soundCollection and keyPressManager.
    This class does not have an understanding of key-presses, only of sounds (except for _updateSoundboardConfiguration(), but I had to put that somewhere)
    """


    def __init__(self, soundCollection, keyPressManager, recorder):
        """

        :type soundCollection: SoundCollection
        :type keyPressManager: KeyPressManager
        """
        self.soundCollection = soundCollection
        self.keyPressManager = keyPressManager
        self.recorder = recorder
        self.hold_to_play = False
        self.pause_soundboard = False
        self.previous_sounds_queue = [next(iter(soundCollection.key_bind_map.values())), next(iter(soundCollection.key_bind_map.values()))] # cannot have null values


    def runpyHookThread(self):
        hm = pyHook.HookManager()
        hm.KeyDown = self.handleKeyEvent
        hm.KeyUp = self.handleKeyEvent
        hm.HookKeyboard()
        # try:
        #     pythoncom.PumpMessages()
        # except KeyboardInterrupt:
        #     pass


    def handleKeyEvent(self, key_event):
        self.keyPressManager.processKeyEvent(key_event) # update data inside of keyPressManager about what key was pressed
        if self.keyPressManager.key_state_changed and not keyPressManager.last_event_was_key_release:
            self.recorder.processKeysDown(self.keyPressManager.getKeysDown()) # recorder class will start or stop recording if the recording hotkeys were pressed
            self._updateSoundboardConfiguration() # use the now updated data stored inside of keyPressManager to update the configuration settings of the soundboard
            possible_new_sound_entry = self.soundCollection.getBestSoundEntryMatchOrNull(self.keyPressManager.getKeysDown())
            self.addSoundToQueueAndPlayIt(possible_new_sound_entry)

        return True

    def addSoundToQueueAndPlayIt(self, sound_entry):
        self.updateQueueWithNewSoundEntry(sound_entry)
        # if the soundboard is on and a key (which wasn't already down before) for a sound was pressed.
        if not self.pause_soundboard and sound_entry is not None:
            self.soundCollection.playSoundToFinish(self.getCurrentSoundEntry())

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



    def _updateSoundboardConfiguration(self):
        if keyPressManager.endingKeysEqual(["pause"]):
            self.pause_soundboard = not self.pause_soundboard
            self.soundCollection.stopAllSounds()
        elif self.pause_soundboard: # break early if soundboard is paused
            return


        elif self.keyPressManager.keysAreContainedInKeysDown(["1", "4"]):  # we use more lenient matching for this one
            thread.start_new_thread(self.getCurrentSoundEntry().jumpToMarkedFrameIndex, tuple())  # need to call via a thread so we don't get blocked by the .play() which can get called by this function
        if self.keyPressManager.keysAreContainedInKeysDown(["tab", "4"]):  # we use more lenient matching for this one
            thread.start_new_thread(self.getCurrentSoundEntry().jumpToSecondaryMarkedFrameIndex, tuple())  # need to call via a thread so we don't get blocked by the .play() which can get called by this function
        elif self.keyPressManager.keysAreContainedInKeysDown(["1", "7"]):
            thread.start_new_thread(self.getCurrentSoundEntry().resumePlayingBeforeLastJump, tuple())  # need to call via a thread so we don't get blocked by the .play() which can get called by this function


        if len(self.keyPressManager.getKeysDown()) >= 2 and self.keyPressManager.getKeysDown()[0] == "menu" and self.keyPressManager.getKeysDown()[-1] in PITCH_MODIFIERS:
            self.getCurrentSoundEntry().pitch_modifier = PITCH_MODIFIERS[self.keyPressManager.getKeysDown()[-1]]
            thread.start_new_thread(self.getCurrentSoundEntry().jumpToMarkedFrameIndex, tuple()) # need to call via a thread so we don't get blocked by the .play() which can get called by this function

       # key binds that affect all sounds in the sound collection
        elif keyPressManager.endingKeysEqual(["tab", "return"]): # tab + enter -> clear non-playing sounds from the "recent sounds queue"
            print "self.clearAllNonPlayingSoundsFromTheFrontOfPreviousSoundsQueue()"
            self.clearAllNonPlayingSoundsFromTheFrontOfPreviousSoundsQueue()
        elif self.keyPressManager.endingKeysEqual(["return"]): # enter -> stop all currently playing sounds
            self.soundCollection.stopAllSounds()
        elif self.keyPressManager.endingKeysEqual(["left", "right"]): # left + right -> reset pitch of all sounds
            self.soundCollection.resetAllPitches()
        elif keyPressManager.endingKeysEqual(["tab", "left"]):
            self.recorder.selectPrevRecording()
        elif keyPressManager.endingKeysEqual(["tab", "right"]):
            self.recorder.selectNextRecording()
        elif keyPressManager.endingKeysEqual(["tab", "delete"]):
            self.recorder.deleteCurrRecording()
        elif self.keyPressManager.endingKeysEqual(["menu", "left"]): # alt + left -> shift down pitch of currently playing sound
            self.soundCollection.shiftAllPitches(-PITCH_SHIFT_AMOUNT)
        elif self.keyPressManager.endingKeysEqual(["menu", "right"]): # alt + right (insert trump joke here xd) -> shift down pitch of currently playing sound
            self.soundCollection.shiftAllPitches(PITCH_SHIFT_AMOUNT)
        elif self.keyPressManager.endingKeysEqual(["left"]): # left (without alt) -> shift down pitch of all sounds
            self.getCurrentSoundEntry().shiftPitch(-PITCH_SHIFT_AMOUNT)
        elif self.keyPressManager.endingKeysEqual(["right"]): # right (without alt) -> shift up pitch of all sounds
            self.getCurrentSoundEntry().shiftPitch(PITCH_SHIFT_AMOUNT)

        # elif self.keyPressManager.endingKeysEqual(["1","2","3"]):
        #     self.hold_to_play = not self.hold_to_play



        # key binds that affect the last sound played
        elif self.keyPressManager.endingKeysEqual(["tab", "down"]):
            self.getCurrentSoundEntry().activateSlowMotion()
        elif self.keyPressManager.endingKeysEqual(["tab", "up"]):
            self.getCurrentSoundEntry().activateSpeedUpMotion()
        elif self.keyPressManager.endingKeysEqual(["tab","\\"]) or self.keyPressManager.endingKeysEqual(["tab", "2"]):
            self.getCurrentSoundEntry().activateOscillate()
        elif self.keyPressManager.endingKeysEqual(["tab", "["]):
            self.getCurrentSoundEntry().frames_between_oscillate_shifts -= 1
            print "oscillate peak:", self.getCurrentSoundEntry().frames_between_oscillate_shifts
        elif self.keyPressManager.endingKeysEqual(["tab", "]"]):
            self.getCurrentSoundEntry().frames_between_oscillate_shifts += 1
            print "oscillate peak:", self.getCurrentSoundEntry().frames_between_oscillate_shifts
        elif self.keyPressManager.endingKeysEqual(["tab", "o"]):
            self.getCurrentSoundEntry().oscillate_shift -= .01
            print "oscillate amount:", self.getCurrentSoundEntry().oscillate_shift
        elif self.keyPressManager.endingKeysEqual(["tab", "p"]):
            self.getCurrentSoundEntry().oscillate_shift += .01
            print "oscillate amount:", self.getCurrentSoundEntry().oscillate_shift
        elif self.keyPressManager.endingKeysEqual(["up"]):
            self.getCurrentSoundEntry().moveMarkedFrameIndex(SHIFT_SECONDS)
        elif self.keyPressManager.endingKeysEqual(["down"]):
            self.getCurrentSoundEntry().moveMarkedFrameIndex(-SHIFT_SECONDS)
        elif self.keyPressManager.endingKeysEqual(["1","3"]):
            self.getCurrentSoundEntry().markCurrentFrameIndex()
        elif self.keyPressManager.endingKeysEqual(["tab", "3"]):
            self.getCurrentSoundEntry().markSecondaryFrameIndex()
        elif self.keyPressManager.endingKeysEqual(["1", "2"]):
            self.swapCurrentAndPreviousSoundEntry()
        elif self.keyPressManager.endingKeysEqual(["`"]):
             self.getCurrentSoundEntry().stop() # no new thread needed
        elif self.keyPressManager.endingKeysEqual(["1", "6"]) :
            self.soundCollection.playSoundToFinish(self.getCurrentSoundEntry())
        elif self.keyPressManager.endingKeysEqual(["1", "5"]):
            if self.getCurrentSoundEntry().is_playing:
                self.getCurrentSoundEntry().markCurrentFrameIndex()
                self.getCurrentSoundEntry().stop()
            else:
                self.getCurrentSoundEntry().reset_frame_index_on_play = False
                self.soundCollection.playSoundToFinish(self.getCurrentSoundEntry())
        elif self.keyPressManager.endingKeysEqual(["2", "5"]):
            if not self.getCurrentSoundEntry().is_playing:
                self.soundCollection.playSoundToFinish(self.getCurrentSoundEntry())
            else:
                self.getCurrentSoundEntry().reverse_mode = not self.getCurrentSoundEntry().reverse_mode
        elif self.keyPressManager.endingKeysEqual(["tab", "1"]): # stop current sound, swap to last sound and start playing
            self.getCurrentSoundEntry().stop()
            self.swapCurrentAndPreviousSoundEntry()
            self.getCurrentSoundEntry().reset_frame_index_on_play = False
            self.soundCollection.playSoundToFinish(self.getCurrentSoundEntry())
        # elif self.keyPressManager.endingKeysEqual(["tab", "6"]):
        #     self.getCurrentSoundEntry().matchBpmWithAnotherSound(self.getPreviousSoundEntry())
        # elif self.keyPressManager.endingKeysEqual(["tab", "7"]):
        #     self.getCurrentSoundEntry().autoDetectBpm()
        # elif self.keyPressManager.endingKeysEqual(["tab", "q"]):
        #     self.getCurrentSoundEntry().bpm_obj.update()
        #     print self.getCurrentSoundEntry().bpm_obj.avg_bpm
        # elif self.keyPressManager.endingKeysEqual(["tab", "w"]):
        #     self.getCurrentSoundEntry().bpm = self.getCurrentSoundEntry().bpm_obj.avg_bpm
        # elif self.keyPressManager.endingKeysEqual(["tab", "e"]):
        #     self.getCurrentSoundEntry().bpm_obj.restart()
        elif self.keyPressManager.endingKeysEqual(["tab", "r"]):
            PitchController.oscillateSound(self.getCurrentSoundEntry())
        elif self.keyPressManager.endingKeysEqual(["tab", "q"]):
            PitchController.oscillate_amplitude  *= .75
            print "oscillate_amplitude", PitchController.oscillate_amplitude
        elif self.keyPressManager.endingKeysEqual(["tab", "w"]):
            PitchController.oscillate_amplitude *= 1.25
            print "oscillate_amplitude", PitchController.oscillate_amplitude
        elif self.keyPressManager.endingKeysEqual(["tab", "a"]):
            PitchController.oscillate_pitch_shift_per_second *= .75
            print "oscillate_pitch_shift_per_second", PitchController.oscillate_pitch_shift_per_second
        elif self.keyPressManager.endingKeysEqual(["tab", "s"]):
            PitchController.oscillate_pitch_shift_per_second *= 1.25
            print "oscillate_pitch_shift_per_second", PitchController.oscillate_pitch_shift_per_second
        elif self.keyPressManager.endingKeysEqual(["tab", "e"]):
            PitchController.gradualPitchShiftSound(self.getCurrentSoundEntry(), 1)
        elif self.keyPressManager.endingKeysEqual(["tab", "d"]):
            PitchController.gradualPitchShiftSound(self.getCurrentSoundEntry(), -1)

    def updateQueueWithNewSoundEntry(self, sound_entry_to_add):
        if self.getCurrentSoundEntry() != sound_entry_to_add and sound_entry_to_add is not None:
            if len(self.previous_sounds_queue) >= SOUND_QUEUE_MAX_SIZE:
                del(self.previous_sounds_queue[0])
            self.previous_sounds_queue.append(sound_entry_to_add)



if __name__ == "__main__":
    soundLibrary = SoundLibrary(SOUNDBOARD_JSON_FILE, SOUNDBOARD_SOUNDS_BASE_FOLDER_PATH)
    soundCollection = SoundCollection(soundLibrary)
    for key_bind in soundCollection.key_bind_map:
        print list(key_bind), os.path.basename(soundCollection.key_bind_map[key_bind].path_to_sound)

    keyPressManager = KeyPressManager()

    audioRecorder = AudioRecorder(soundCollection)
    soundboardController = SoundBoardController(soundCollection, keyPressManager, audioRecorder)
    soundBoardGUI = SoundBoardGUI(soundCollection, keyPressManager, audioRecorder, soundboardController, soundLibrary)

    soundBoardGUI.root.after(1000, soundboardController.runpyHookThread)
    thread.start_new_thread(audioRecorder.listen, tuple())
    soundBoardGUI.runGUI()




