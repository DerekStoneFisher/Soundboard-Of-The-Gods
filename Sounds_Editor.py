import tkinter as tk
import tkinter.font as tkFont
import json, os
from Audio_Proj_Const import KEY_ID_TO_NAME_MAP, convertJavaKeyIDToRegularKeyID, getKeyNames
from KeyPress import KeyPressManager


from Json_Editor import SOUNDBOARD_JSON_FILE

FONT_SIZE = 9

class SoundsEditor:
    def __init__(self, keyPressManager):
        self.sounds = []
        self.current_keys_down = []
        self._buildWindow()
        self.getKeysPressedLabel()
        self._buildListBox()
        self.keyPressManager = keyPressManager
        self.getAddSoundButton()

    def _buildWindow(self):
        self.root = tk.Tk()
        self.root.title("Sounds Editor")
        self.root.geometry("1024x480")
        self.root.configure(background='black')
        default_font = tkFont.nametofont("TkTextFont")
        default_font.configure(size=FONT_SIZE)
        self.root.option_add("*Font", default_font)

    def _buildListBox(self):
        scrollbar = tk.Scrollbar(self.root)
        listbox = tk.Listbox(self.root, yscrollcommand=scrollbar.set, width=64, borderwidth=3)


        with open(SOUNDBOARD_JSON_FILE) as config_file:
            config_object = json.load(config_file)
            soundboard_entries = config_object["soundboardEntries"]
            for soundboard_entry in soundboard_entries:
                sound_path = soundboard_entry["file"].replace("\\", "/")
                sound_name = os.path.basename(sound_path)
                activation_key_codes = soundboard_entry["activationKeysNumbers"]
                activation_key_names = getKeyNames(activation_key_codes)
                listbox.insert(tk.END, str(sound_name) + '    ' + str(activation_key_names))

        listbox.pack(side=tk.LEFT, fill=tk.BOTH)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)

        scrollbar.config(command=listbox.yview)

    def getKeysPressedLabel(self):



    def updateKeysDown(self):
        print('updateKeysDown')
        print(self.keyPressManager.getKeysDown())

    def getAddSoundButton(self):
        canvas = tk.Canvas(self.root, width=1200, height=600)
        canvas.pack()

        update_keys_down = tk.Button(canvas, text='Update Keys Down', command=self.updateKeysDown)
        # update_keys_down.pack(side=tk.TOP)

        new_sound_path_textbox = tk.Entry(canvas, text="New Sound Path")
        add_new_sound_button = tk.Button(canvas, text="Add Sound")

        new_sound_path_textbox.pack(side=tk.LEFT)
        add_new_sound_button.pack(side=tk.LEFT)








if __name__ == '__main__':
    keyPressManager = KeyPressManager()
    editor = SoundsEditor(keyPressManager)
    editor.root.mainloop()