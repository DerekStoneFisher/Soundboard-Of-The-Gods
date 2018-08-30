import tkinter as tk
from functools import partial
import os
import Sound
import thread
import time

SOUNDS_DIRECTORY = "C:/Users/Admin/Desktop/Soundboard/ytp/full ytps"
WIDTH = 15
HEIGHT = 1
ANCHOR='w'
BUTTONS_PER_COLUMN = 10

class SoundBoardGUI:
    def __init__(self, soundCollection, keyPressManager, audioRecorder, soundBoardController):
        self.soundCollection = soundCollection
        self.keyPressManager = keyPressManager # needed to get the most recent key to create new binds
        self.recorder = audioRecorder # needed to get the recordings so we can use them to create new soundEntries
        self.soundBoardController = soundBoardController # so we can call the addSoundToQueueAndPlayIt() function
        self.root = None
        self._buildWindow()

    def runGUI(self):
        self.root.mainloop()

    def _buildWindow(self):
        self.root = tk.Tk()
        self.root.title("Soundboard")
        self.root.geometry("1024x480")
        self.root.configure(background='black')
        #tkinter.Entry(self.window, state=DISABLED)

        row = 0
        column = 0
        for sound_entry in self.soundCollection.sound_entry_list_from_json:
            if column > BUTTONS_PER_COLUMN:
                column = 0
                row += 1
            button = tk.Button(self.root, text=sound_entry.getSoundName(), command=partial(self.soundBoardController.addSoundToQueueAndPlayIt, sound_entry), height=HEIGHT, width=WIDTH, anchor=ANCHOR)
            button.grid(column=column, row=row)
            column += 1

        row += 1
        self.root.grid_rowconfigure(row, minsize=25)
        row += 1
        column = 0

        if os.path.exists(SOUNDS_DIRECTORY):
            for filename in os.listdir(SOUNDS_DIRECTORY):
                if column > BUTTONS_PER_COLUMN:
                    column = 0
                    row += 1
                sound_entry = Sound.SoundEntry(os.path.join(SOUNDS_DIRECTORY, filename))
                self.soundCollection.addSoundEntry(sound_entry)
                button = tk.Button(self.root, text=os.path.basename(filename), width=WIDTH, anchor='w', command=partial(self.soundBoardController.addSoundToQueueAndPlayIt, sound_entry))
                button.grid(column=column, row=row)
                column += 1

            row += 1
            column = 0



        # for i in self.recorder.previous_recordings




        button = tk.Button(self.root, text="stopAllSounds()", command=self.soundCollection.stopAllSounds, width=WIDTH, anchor='w')
        button.grid(column=column, row=row)
        #self.window.withdraw()