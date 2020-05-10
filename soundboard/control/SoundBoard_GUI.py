from soundboard.audio.Sound import SoundEntry
import tkinter as tk
import tkinter.font as tkFont
from functools import partial
from soundboard.audio import Audio_Utils
import os

SOUNDS_DIRECTORY = "C:/Users/Admin/Desktop/Soundboard/Other Music + Godly"
ENTIRE_SOUNDBOARD_DIRECTORY = "C:/Users/Admin/Desktop/Soundboard"
WIDTH = 15
HEIGHT = 1
ANCHOR='w'
BUTTONS_PER_COLUMN = 21
FONT_SIZE = 7
SMALL_FOLDER_LIST = []



class SoundBoardGUI:
    def __init__(self, soundCollection, keyPressManager, audioRecorder, soundBoardController, soundLibrary):
        self.soundCollection = soundCollection
        self.keyPressManager = keyPressManager # needed to get the most recent key to create new binds
        self.recorder = audioRecorder # needed to get the recordings so we can use them to create new soundEntries
        self.soundBoardController = soundBoardController # so we can call the addSoundToQueueAndPlayIt() function
        self.soundLibrary = soundLibrary
        self.saved_keys_down = []

        self.root = tk.Tk()
        self.configWindow()

        canvas1 = tk.Canvas(self.root, background='black')
        canvas2 = tk.Canvas(self.root, background='black')
        self.root.config()
        self.addNewSoundButtons(canvas1)
        self.addSoundboardButtons(canvas2)
        canvas1.pack(fill='both', expand=True, side=tk.TOP)
        canvas2.pack(side=tk.TOP)




    def addNewSoundButtons(self, canvas):

        self.file_name_entry_box = tk.Entry(canvas)
        new_sound_desc = tk.Label(canvas, text='Enter Path')

        self.update_keys_down_button = tk.Button(canvas, text='Update Keys Down', command=self.updateKeysDown)

        self.write_to_file_button = tk.Button(canvas, text='Save Recording', command=self.addSound)

        new_sound_desc.pack(side=tk.LEFT)
        self.file_name_entry_box.pack(side=tk.LEFT)
        self.update_keys_down_button.pack(side=tk.LEFT)
        self.write_to_file_button.pack(side=tk.LEFT)


    def addSound(self):
        sound_path = self.file_name_entry_box.get()
        activation_keys = self.saved_keys_down
        chunks = self.recorder.getCurrentRecording()
        # write the chunks to a file, update the sound collection so we can play it, update the Json so it stays after restarting
        print("addSound soundPath={}, activation_keys={}, chunks={}".format(sound_path, activation_keys, len(chunks)))
        Audio_Utils.writeChunksToFile(chunks, sound_path, False)
        self.soundCollection.createAndAddSoundEntry(sound_path, activation_keys)
        self.soundLibrary.add(sound_path, activation_keys)




    def updateKeysDown(self):
        print('updateKeysDown')
        self.saved_keys_down = self.keyPressManager.getKeysDown()
        # self.saved_keys_down_str_var.set("Saved Keys Down: " + str(self.saved_keys_down))
        print(self.saved_keys_down)

    def configWindow(self):
        self.root.title("Soundboard")
        self.root.geometry("1024x480")
        self.root.configure(background='black')
        default_font = tkFont.nametofont("TkTextFont")
        default_font.configure(size=FONT_SIZE)
        self.root.option_add("*Font", default_font)

    def runGUI(self):
        self.root.mainloop()


    def makeSoundAndPlayIt(self, path_to_sound_entry):
        if path_to_sound_entry not in self.soundCollection.sound_entry_path_map:
            sound_entry = SoundEntry(path_to_sound_entry)
            self.soundCollection.addSoundEntry(sound_entry)
        sound_entry = self.soundCollection.sound_entry_path_map[path_to_sound_entry]
        self.soundBoardController.addSoundToQueueAndPlayIt(sound_entry)

    def addSoundboardButtons(self, parent):

        #tkinter.Entry(self.window, state=DISABLED)

        row = 0
        column = 0
        # for sound_entry in self.soundCollection.sound_entry_list_from_json:
        #     if column > BUTTONS_PER_COLUMN:
        #         column = 0
        #         row += 1
        #     button = tk.Button(self.root, text=sound_entry.getSoundName(), command=partial(self.soundBoardController.addSoundToQueueAndPlayIt, sound_entry), height=HEIGHT, width=WIDTH, anchor=ANCHOR)
        #     button.grid(column=column, row=row)
        #     column += 1
        #
        # row += 1
        # self.root.grid_rowconfigure(row, minsize=25)
        # row += 1
        # column = 0

        if os.path.exists(SOUNDS_DIRECTORY):
            for filename in os.listdir(SOUNDS_DIRECTORY):
                if column > BUTTONS_PER_COLUMN:
                    column = 0
                    row += 1
                sound_path = os.path.join(SOUNDS_DIRECTORY, filename)
                sound_entry = SoundEntry(sound_path)
                self.soundCollection.addSoundEntry(sound_entry)

                background = "white"
                if Audio_Utils.chunksToSeconds(len(sound_entry.chunks)) > 3:
                    background = "red"



                button = tk.Button(parent, text=os.path.basename(filename), width=WIDTH, anchor='w', command=partial(self.makeSoundAndPlayIt, sound_path), background=background)
                button.grid(column=column, row=row)
                column += 1

            row += 1
            column = 0



        # all_wave_files = [dp + "/" + f for dp, dn, filenames in os.walk(ENTIRE_SOUNDBOARD_DIRECTORY) for f in
        #                 filenames if os.path.splitext(f)[1] == '.wav' and dp + "/" + f not in self.soundCollection.sound_entry_path_map.keys()]
        #
        #
        # last_folder = ""
        # for filename in all_wave_files:
        #     filename = filename.replace("\\", "/")
        #     if (filename.split("/")[-3] != last_folder):
        #
        #         row += 1
        #         column = 0
        #     last_folder = filename.split("/")[-3]
        #     if column > BUTTONS_PER_COLUMN:
        #         column = 0
        #         row += 1
        #
        #
        #
        #     sound_path = os.path.join(SOUNDS_DIRECTORY, filename)
        #     seconds = os.path.getsize(sound_path)/float(198656)
        #     # print sound_path, seconds
        #
        #     background = "white"
        #     if seconds > 3:
        #         background = "red"
        #
        #     button = tk.Button(self.root, text=os.path.basename(filename), width=WIDTH, anchor='w', command=partial(self.makeSoundAndPlayIt, sound_path), background=background)
        #     button.grid(column=column, row=row)
        #     column += 1

        folders = []
        if os.path.exists(ENTIRE_SOUNDBOARD_DIRECTORY):
            for directory_path, directory_name, filenames in os.walk(ENTIRE_SOUNDBOARD_DIRECTORY):
                directory_path = directory_path.replace("\\", "/")
                prev_folders = folders
                folders = directory_path.replace(ENTIRE_SOUNDBOARD_DIRECTORY + "/", "").split("/")

                if len(folders)>0 and len(prev_folders)>0 and folders[-1] not in prev_folders[-1]:
                    if len(folders) == 1:
                        row += 1
                        column = 0
                    if len(filenames) > 4:
                        row += 1
                        column = 0

                    folders_copy = folders
                    if len(folders) <= 4:
                        folders_copy = folders[-1:]

                    for folder in folders_copy:
                        button = tk.Button(parent, text=folder, width=WIDTH, anchor='w',background='yellow')
                        button.grid(column=column, row=row)
                        column+=1



                if (
                                'skrillex' in folders and 'skrillex' not in prev_folders) or (
                                'skrillex' in prev_folders and 'skrillex' not in folders) or (
                                'rap' in folders and 'rap' not in prev_folders) or (
                                'rap' in prev_folders and 'rap' not in folders):
                    row += 1
                    column = 0
                elif 'Other Music + Godly' in folders:
                    continue



                for filename in filenames:
                    if column > BUTTONS_PER_COLUMN:
                        column = 0
                        row += 1

                    sound_path = directory_path + "/" + filename
                    is_wav_file = os.path.splitext(filename)[1] == '.wav'
                    is_already_in_soundboard = directory_path + "/" + filename not in self.soundCollection.sound_entry_path_map.keys()

                    background = "white"
                    if is_wav_file:
                        seconds = os.path.getsize(sound_path) / float(198656)
                        if 'skrillex' in folders:
                            background = "green"
                        elif 'rap' in folders:
                            background = "orange"
                        elif seconds > 6:
                            background = "red"

                        button = tk.Button(parent, text=os.path.basename(filename), width=WIDTH, anchor='w',
                                           command=partial(self.makeSoundAndPlayIt, sound_path),
                                           background=background)
                        button.grid(column=column, row=row)
                        column += 1


            row += 1
            column = 0

        # for i in self.recorder.previous_recordings




        button = tk.Button(parent, text="stopAllSounds()", command=self.soundCollection.stopAllSounds, width=WIDTH, anchor='w')
        button.grid(column=column, row=row)
        #self.window.withdraw()