from tkinter import *
from functools import partial
import os
import Sound
import thread
import time

SOUNDS_DIRECTORY = "sounds"
WIDTH = 10
ANCHOR='w'

class SoundBoardGUI:
    def __init__(self, soundCollection, keyPressManager, audioRecorder):
        self.soundCollection = soundCollection
        self.keyPressManager = keyPressManager # needed to get the most recent key to create new binds
        self.recorder = audioRecorder # needed to get the recordings so we can use them to create new soundEntries
        self.window = None
        self._buildWindow()

    def runGUI(self):
        self.window.mainloop()

    def _buildWindow(self):
        self.window = Tk()
        self.window.title("Soundboard")
        self.window.geometry("640x480")
        self.window.configure(background='black')

        row = 0
        column = 0
        for key_bind,sound_entry in self.soundCollection.key_bind_map.iteritems():
            button = Button(self.window, text=sound_entry.getSoundName(), command=partial(self.soundCollection.playSoundToFinish, sound_entry), width=WIDTH, anchor='w')
            button.grid(column=column, row=row)
            column += 1

        row += 1
        column = 0

        for filename in os.listdir("sounds"):
            button = Button(self.window, text=os.path.basename(filename), width=WIDTH, anchor='w')
            button.grid(column=column, row=row)
            column += 1

        row += 1
        column = 0



        # for i in self.recorder.previous_recordings




        button = Button(self.window, text="stopAllSounds()", command=self.soundCollection.stopAllSounds, width=WIDTH, anchor='w')
        button.grid(column=column, row=row)