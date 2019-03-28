import json, os
from collections import OrderedDict
from Audio_Proj_Const import convertJavaKeyIDToRegularKeyID, KEY_ID_TO_NAME_MAP
# SOUNDBOARD_BASE_DIRECTORY = "C:/Users/Admin/Desktop/Soundboard"
SOUNDBOARD_BASE_DIRECTORY = "D:/DerekProjects/Python_Script_Stuff/Audio_Recorder/sounds/pretend soundboard folder"
SOUNDBOARD_JSON_FILE = "D:/DerekProjects/Python_Script_Stuff/Audio_Recorder/sounds/pretend soundboard folder/pretend soundboard file.json"
SOUNDBOARD_JSON_FILE_EDITED = "D:/DerekProjects/Python_Script_Stuff/Audio_Recorder/sounds/pretend soundboard folder/pretend soundboard file_edited.json"
BOARD2 = "Board2.json"

class JsonEditor:
    def __init__(self):
        self.sound_name_to_folder_sound_path_map = OrderedDict() # { name -> path } for sounds in the soundboard folder
        self.sound_name_to_json_sound_path_map = OrderedDict() # { name -> path } for sounds in the soundboard json file
        self.sound_name_to_activation_keys_map = OrderedDict() # { name -> activation_keys } for sounds in the json file

        # sounds which have no activation keys bound to them, but they appear in the soundboard folder
        self.unassigned_sound_names_to_paths_map = OrderedDict()


    def runJsonUpdateRoutine(self, json_config_file_path=SOUNDBOARD_JSON_FILE, json_config_new_file_path=SOUNDBOARD_JSON_FILE_EDITED, soundboard_folder_path=SOUNDBOARD_BASE_DIRECTORY):
        self._populateSoundMapFromSoundboardFolder(soundboard_folder_path)
        self._populateSoundMapFromJson(json_config_file_path)
        self._updateJsonSoundPathMapWithActualSoundPathMap()
        self._updateJsonWithNewFileLocations(json_config_new_file_path)
        self._updateUnassignedSoundsMap()


    def _populateSoundMapFromSoundboardFolder(self, soundboard_base_directory):
        for directory_path, directory_name, filenames in os.walk(soundboard_base_directory):
            for filename in filenames:
                if filename.endswith(".wav"):
                    sound_path = (directory_path + "/" + filename).replace("\\", "/")
                    if filename in self.sound_name_to_folder_sound_path_map:
                        print "FILE-DUPE\toverwriting", filename, "sound_path of\t", self.sound_name_to_folder_sound_path_map[filename], "\twith\t", sound_path
                    self.sound_name_to_folder_sound_path_map[filename] = sound_path



    def _populateSoundMapFromJson(self, config_file_path):
        with open(config_file_path) as config_file:
            config_object = json.load(config_file)
            soundboard_entries = config_object["soundboardEntries"]
            for soundboard_entry in soundboard_entries:
                try:
                    sound_path = soundboard_entry["file"].replace("\\", "/")
                    sound_name = os.path.basename(sound_path)
                    activation_key_codes = soundboard_entry["activationKeysNumbers"]

                    if sound_name in self.sound_name_to_json_sound_path_map:
                        print "JSON-DUPE\toverwriting", sound_name, "activation code", self.sound_name_to_activation_keys_map[sound_name], "with", activation_key_codes
                    self.sound_name_to_json_sound_path_map[sound_name] = sound_path
                    self.sound_name_to_activation_keys_map[sound_name] = activation_key_codes
                except:
                    print "failed to ingest", soundboard_entry["file"]


    def _updateJsonSoundPathMapWithActualSoundPathMap(self):
        for sound_name, json_sound_path in self.sound_name_to_json_sound_path_map.items():
            activation_keys = self.sound_name_to_activation_keys_map[sound_name]
            if not os.path.exists(json_sound_path):
                if sound_name in self.sound_name_to_folder_sound_path_map:
                    new_sound_path = self.sound_name_to_folder_sound_path_map[sound_name]
                    print "MOVED    \t", sound_name, "does not exist in the json specified location of\t", json_sound_path, "\tso it is being changed to\t", new_sound_path, "\twith activation keys", activation_keys
                    self.sound_name_to_json_sound_path_map[sound_name] = new_sound_path
                else:
                    print "NOT-FOUND\t", sound_name, "does not exist in the soundboard directory. The path specified by the json file is", json_sound_path
            else:
                print "UNCHANGED\t", sound_name, "at", json_sound_path

    def _updateJsonWithNewFileLocations(self, new_config_file_path):
        base_dict = dict()
        base_dict["soundboardEntries"] = []

        for sound_name, sound_path in self.sound_name_to_json_sound_path_map.items():
            activation_keys = self.sound_name_to_activation_keys_map[sound_name]
            inner_dict = OrderedDict()
            inner_dict["file"] = sound_path.replace("/", "\\")
            inner_dict["activationKeysNumbers"] = activation_keys
            base_dict["soundboardEntries"].append(inner_dict)

        with open(new_config_file_path, "w") as f:
            f.write(json.dumps(base_dict).replace('{"file"', '\n\t{"file"'))
    
    def _updateUnassignedSoundsMap(self):
        for name, path in self.sound_name_to_folder_sound_path_map.items():
            if name not in self.sound_name_to_activation_keys_map:
                self.unassigned_sound_names_to_paths_map[name] = path
    
    
    def createKeyNameJsonFromEditedJson(self, edited_json_file_path=SOUNDBOARD_JSON_FILE_EDITED, new_json_file_path=BOARD2):
        with open(edited_json_file_path, 'r') as json_file:
            json_obj = json.load(json_file)
    
        new_json = dict()
        new_json["soundboardEntries"] = []
        for d in json_obj["soundboardEntries"]:
            activation_key_numbers = d['activationKeysNumbers']
            regular_key_numbers = [convertJavaKeyIDToRegularKeyID(key) for key in activation_key_numbers]
    
            skip = False
            key_names = []
            for regular_key_num in regular_key_numbers:
                if regular_key_num in KEY_ID_TO_NAME_MAP:
                    key_names.append(KEY_ID_TO_NAME_MAP[regular_key_num].lower())
                else:
                    print "invalid key num {} for sound {} found in json, not adding sound".format(regular_key_num, d['file'])
                    skip = True
    
            if not skip:
                new_d = OrderedDict()
                new_d['file'] = d['file']
                new_d['activationKeyNames'] = key_names
                new_json["soundboardEntries"].append(new_d)
    
        with open(new_json_file_path, 'w') as output:
            output.write(json.dumps(new_json, output).replace('{"file"', '\n\t{"file"').replace("\\\\", "/"))
    

if __name__ == "__main__":
    json_editor = JsonEditor()
    json_editor.runJsonUpdateRoutine(SOUNDBOARD_JSON_FILE, SOUNDBOARD_JSON_FILE_EDITED, SOUNDBOARD_BASE_DIRECTORY)
    json_editor.createKeyNameJsonFromEditedJson(SOUNDBOARD_JSON_FILE_EDITED, BOARD2)
