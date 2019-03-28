# from Sound import SoundEntry
import json
import os
from Json_Editor import JsonEditor
from collections import OrderedDict

class SoundLibrary:
    '''
    The Sound Library contains all of the sounds in the Board JSON file
    It has the power to add sounds to the JSON file, edit activation keys for sounds in the JSON file, and delete sounds from the JSON file
    It only deals with key names only, no key codes. It will not have an edited version.
    '''
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        self.refresh() # self.config_object = json.load(...)
        self.unassigned_sounds = OrderedDict()
        self.recordings = []


    def entries(self):
        return self.config_object["soundboardEntries"]

    def save(self):
        with open(self.json_file_path, 'w') as json_file:
            json.dump(self.config_object, json_file)

    def refresh(self):
        with open(self.json_file_path, 'r') as json_file:
            self.config_object = json.load(json_file)


    def deleteByPath(self, path_to_sound, save=True):
        old_len = len(self.entries())
        self.config_object["soundboardEntries"] = [
            entry for entry in self.entries()
            if not entry['file'] == path_to_sound
        ]
        print("DEBUG: deleted {} entries with path_to_sound {} from json".format(old_len - len(self.entries()), path_to_sound))
        if save:
            self.save()

    def deleteByName(self, sound_name, save=True):
        old_len = len(self.entries())
        self.config_object["soundboardEntries"] = [
            entry for entry in self.entries()
            if not os.path.basename(entry['file']) == os.path.basename(sound_name)
        ]
        print("DEBUG: deleted {} entries with sound_name {} from json".format(old_len - len(self.entries()), sound_name))
        if save:
            self.save()



    def add(self, path_to_sound, activation_keys, save=True):
        new_entry = dict()
        new_entry['file'] = path_to_sound
        new_entry['activationKeyNames'] = activation_keys
        self.entries().append(new_entry)
        if save:
            self.save()

if __name__ == '__main__':
    json_editor = JsonEditor()
    json_editor.runJsonUpdateRoutine()
    json_editor.createKeyNameJsonFromEditedJson()

    soundLibrary = SoundLibrary('Board2.json')
    soundLibrary.unassigned_sounds = json_editor.unassigned_sound_names_to_paths_map

    def printEntries():
        for entry in soundLibrary.entries():
            print(entry)

    printEntries()
    print("add")
    soundLibrary.add("C:/test_sound", ['a','b','c'])
    printEntries()
    print("delete")
    soundLibrary.deleteByName("test_sound")
    printEntries()

