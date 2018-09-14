import tkinter as tk
import tkinter.font as tkFont
from functools import partial
import os
import Sound
import thread
import time

SOUNDS_DIRECTORY = "C:/Users/Admin/Desktop/Soundboard/ytp/full ytps"
ENTIRE_SOUNDBOARD_DIRECTORY = "C:/Users/Admin/Desktop/Soundboard"
WIDTH = 15
HEIGHT = 1
ANCHOR='w'
BUTTONS_PER_COLUMN = 15
FONT_SIZE = 8



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


    def makeSoundAndPlayIt(self, path_to_sound_entry):
        if path_to_sound_entry not in self.soundCollection.sound_entry_path_map:
            sound_entry = Sound.SoundEntry(path_to_sound_entry)
            self.soundCollection.addSoundEntry(sound_entry)
        sound_entry = self.soundCollection.sound_entry_path_map[path_to_sound_entry]
        self.soundBoardController.addSoundToQueueAndPlayIt(sound_entry)

    def _buildWindow(self):
        self.root = tk.Tk()
        self.root.title("Soundboard")
        self.root.geometry("1024x480")
        self.root.configure(background='black')
        default_font = tkFont.nametofont("TkTextFont")
        default_font.configure(size=FONT_SIZE)
        self.root.option_add("*Font", default_font)
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
                sound_path = os.path.join(SOUNDS_DIRECTORY, filename)
                sound_entry = Sound.SoundEntry(sound_path)
                self.soundCollection.addSoundEntry(sound_entry)

                background = "white"
                if sound_entry.getLengthOfSoundInSeconds() > 3:
                    background = "red"



                button = tk.Button(self.root, text=os.path.basename(filename), width=WIDTH, anchor='w', command=partial(self.makeSoundAndPlayIt, sound_path), background=background)
                button.grid(column=column, row=row)
                column += 1

            row += 1
            column = 0

        if os.path.exists(ENTIRE_SOUNDBOARD_DIRECTORY):
            all_wave_files = [dp + "/" + f for dp, dn, filenames in os.walk(ENTIRE_SOUNDBOARD_DIRECTORY) for f in
                            filenames if os.path.splitext(f)[1] == '.wav' and dp + "/" + f not in self.soundCollection.key_bind_map.values()]

            for filename in all_wave_files:
                if column > BUTTONS_PER_COLUMN:
                    column = 0
                    row += 1

                sound_path = os.path.join(SOUNDS_DIRECTORY, filename)
                button = tk.Button(self.root, text=os.path.basename(filename), width=WIDTH, anchor='w', command=partial(self.makeSoundAndPlayIt, sound_path))
                button.grid(column=column, row=row)
                column += 1

            row += 1
            column = 0

        # for i in self.recorder.previous_recordings




        button = tk.Button(self.root, text="stopAllSounds()", command=self.soundCollection.stopAllSounds, width=WIDTH, anchor='w')
        button.grid(column=column, row=row)
        #self.window.withdraw()