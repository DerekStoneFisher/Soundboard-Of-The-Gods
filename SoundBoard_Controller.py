import os
import Audio_Utils
import threading
from SoundBoard_GUI import SoundBoardGUI
import pythoncom
import pyHook
from Recorder import AudioRecorder

from Sound import SoundEntry, SoundCollection
from KeyPress import KeyPressManager
import thread

SOUND_QUEUE_MAX_SIZE = 5
PITCH_MODIFIERS = {'1':-.75, '2':-.6, '3':-.45, '4':-.3, '5':-.15, '6':0, '7':.15, '8':.3, '9':.45, '0':.6} # how much is the pitch shifted for each step in "piano-mode"
PITCH_SHIFT_AMOUNT = .1 # what multiplier is used to adjust the pitch with the left and right arrows
SHIFT_SECONDS = .15 # by how many seconds will the up and down arrows move the marked frame index


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
            self.recorder.processKeysDown(self.keyPressManager.getKeysDown(), soundCollection) # recorder class will start or stop recording if the recording hotkeys were pressed
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
        self.previous_sounds_queue[-1], self.previous_sounds_queue[-2] = self.previous_sounds_queue[-2], self.previous_sounds_queue[-1]

    def _updateSoundboardConfiguration(self):
        if self.keyPressManager.keysAreContainedInKeysDown(["1", "4"]):  # we use more lenient matching for this one
            thread.start_new_thread(self.getCurrentSoundEntry().jumpToMarkedFrameIndex,tuple())  # need to call via a thread so we don't get blocked by the .play() which can get called by this function

        if len(self.keyPressManager.getKeysDown()) >= 2 and self.keyPressManager.getKeysDown()[0] == "menu" and self.keyPressManager.getKeysDown()[-1] in PITCH_MODIFIERS:
            self.getCurrentSoundEntry().pitch_modifier = PITCH_MODIFIERS[self.keyPressManager.getKeysDown()[-1]]
            thread.start_new_thread(self.getCurrentSoundEntry().jumpToMarkedFrameIndex, tuple()) # need to call via a thread so we don't get blocked by the .play() which can get called by this function

       # key binds that affect all sounds in the sound collection
        elif self.keyPressManager.endingKeysEqual(["return"]): # enter -> stop all currently playing sounds
            self.soundCollection.stopAllSounds()
        elif self.keyPressManager.endingKeysEqual(["left", "right"]): # left + right -> reset pitch of all sounds
            self.soundCollection.resetAllPitches()
        elif self.keyPressManager.endingKeysEqual(["menu", "left"]): # alt + left -> shift down pitch of currently playing sound
            self.soundCollection.shiftAllPitches(-PITCH_SHIFT_AMOUNT)
        elif self.keyPressManager.endingKeysEqual(["menu", "right"]): # alt + right (insert trump joke here xd) -> shift down pitch of currently playing sound
            self.soundCollection.shiftAllPitches(PITCH_SHIFT_AMOUNT)
        elif self.keyPressManager.endingKeysEqual(["left"]): # left (without alt) -> shift down pitch of all sounds
            self.getCurrentSoundEntry().shiftPitch(-PITCH_SHIFT_AMOUNT)
        elif self.keyPressManager.endingKeysEqual(["right"]): # right (without alt) -> shift up pitch of all sounds
            self.getCurrentSoundEntry().shiftPitch(PITCH_SHIFT_AMOUNT)

        # non-sound specific configuration key binds
        elif self.keyPressManager.endingKeysEqual(["2","3","4"]) or keyPressManager.endingKeysEqual(["pause"]):
            self.pause_soundboard = not self.pause_soundboard
            self.soundCollection.stopAllSounds()
        elif self.keyPressManager.endingKeysEqual(["1","2","3"]):
            self.hold_to_play = not self.hold_to_play



        # key binds that affect the last sound played
        elif self.keyPressManager.endingKeysEqual(["tab", "down"]):
            self.getCurrentSoundEntry().activateSlowMotion()
        elif self.keyPressManager.endingKeysEqual(["tab", "up"]):
            self.getCurrentSoundEntry().activateSpeedUpMotion()
        elif self.keyPressManager.endingKeysEqual(["tab","oem_5"] or self.keyPressManager.endingKeysEqual("oem_5")): # tab \
            self.getCurrentSoundEntry().activateOscillate()
        elif self.keyPressManager.endingKeysEqual(["tab", "oem_4"]): # tab [
            self.getCurrentSoundEntry().oscillate_shift += .01
        elif self.keyPressManager.endingKeysEqual(["tab", "oem_6"]): # tab ]
            self.getCurrentSoundEntry().oscillate_shift -= .01
        elif self.keyPressManager.endingKeysEqual(["up"]):
            self.getCurrentSoundEntry().moveMarkedFrameIndex(SHIFT_SECONDS)
        elif self.keyPressManager.endingKeysEqual(["down"]):
            self.getCurrentSoundEntry().moveMarkedFrameIndex(-SHIFT_SECONDS)
        elif self.keyPressManager.endingKeysEqual(["1","3"]):
            self.getCurrentSoundEntry().markCurrentFrameIndex()
        elif self.keyPressManager.endingKeysEqual(["1", "2"]):
            self.swapCurrentAndPreviousSoundEntry()
        elif self.keyPressManager.endingKeysEqual(["1", "5"]) or self.keyPressManager.endingKeysEqual(["oem_3"]):
            self.getCurrentSoundEntry().stop() # no new thread needed
        elif self.keyPressManager.endingKeysEqual(["1", "6"]) :
            self.soundCollection.playSoundToFinish(self.getCurrentSoundEntry())


    def updateQueueWithNewSoundEntry(self, sound_entry_to_add):
        if self.getCurrentSoundEntry() != sound_entry_to_add and sound_entry_to_add is not None:
            if len(self.previous_sounds_queue) >= SOUND_QUEUE_MAX_SIZE:
                del(self.previous_sounds_queue[0])
            self.previous_sounds_queue.append(sound_entry_to_add)



if __name__ == "__main__":
    soundCollection = SoundCollection()
    soundCollection.ingestSoundboardJsonConfigFile("Board1.json")
    for key_bind in soundCollection.key_bind_map:
        print key_bind, os.path.basename(soundCollection.key_bind_map[key_bind].path_to_sound)
    keyPressManager = KeyPressManager()
    audioRecorder = AudioRecorder()
    soundboardController = SoundBoardController(soundCollection, keyPressManager, audioRecorder)
    soundBoardGUI = SoundBoardGUI(soundCollection, keyPressManager, audioRecorder, soundboardController)

    soundBoardGUI.root.after(1000, soundboardController.runpyHookThread)
    thread.start_new_thread(audioRecorder.listen, tuple())
    soundBoardGUI.runGUI()




