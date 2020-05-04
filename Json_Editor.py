import json, os
from collections import OrderedDict
from Audio_Proj_Const import KEY_NAMES, NAME_OVERRIDE_LIST

class JsonEditor:
    '''
    Updates the soundboard config json by updating the file paths of any moved sound files

    This module acts like a script which follows the following steps
    1. Traverses the base directory where all soundboard sounds are stored and extracts the names and paths of all sounds found within.
    2. Extracts the names, paths, and activation keys of each sound from the soundboard JSON config file.
       (Ignores sounds with invalid activation key names. key names are replaced with their version from NAME_OVERRIDE_LIST).
    3. Iterate through each sound found in the JSON config file, applying one of the three changes
        - MOVED: The file path for a sound specified in the JSON does not exist, but there exists as corresponding
                 file path for that same sound found in the soundboard sound directory, so the path is updated accordingly
        - NOT-FOUND: The file for a specified sound in the JSON does not exist, and that sound name was not found
                 in the sound directory either, so it won't be passed into the soundboard on startup
        - UNCHANGED: the file for a specified sound in the JSON exists, so no issues.

    '''
    def __init__(self):
        self.sound_name_to_folder_sound_path_map = OrderedDict() # { name -> path } for sounds in the soundboard folder
        self.sound_name_to_json_sound_path_map = OrderedDict() # { name -> path } for sounds in the soundboard json file
        self.sound_name_to_activation_keys_map = OrderedDict() # { name -> activation_keys } for sounds in the json file

        # sounds which have no activation keys bound to them, but they appear in the soundboard folder
        self.unassigned_sound_names_to_paths_map = OrderedDict()


    def runJsonUpdateRoutine(self, json_config_file_path, json_config_new_file_path, soundboard_folder_path):
        self._populateSoundMapFromSoundboardFolder(soundboard_folder_path)
        self._populateSoundMapFromJson(json_config_file_path)
        self._updateJsonSoundPathMapWithActualSoundPathMap()
        self._updateJsonWithNewFileLocations(json_config_new_file_path)
        self._updateUnassignedSoundsMap()


    def _populateSoundMapFromSoundboardFolder(self, soundboard_base_directory):
        for directory_path, directory_name, filenames in os.walk(soundboard_base_directory):
            for filename in filenames:
                if filename.endswith(".wav"):
                    sound_path = os.path.join(directory_path, filename)
                    if filename in self.sound_name_to_folder_sound_path_map:
                        print "FILE-DUPE\toverwriting", filename, "sound_path of\t", self.sound_name_to_folder_sound_path_map[filename], "\twith\t", sound_path
                    self.sound_name_to_folder_sound_path_map[filename] = sound_path



    def _populateSoundMapFromJson(self, config_file_path):
        with open(config_file_path) as config_file:
            config_object = json.load(config_file)
            soundboard_entries = config_object["soundboardEntries"]
            for soundboard_entry in soundboard_entries:
                try:
                    sound_path = soundboard_entry["file"]
                    sound_name = os.path.basename(sound_path)
                    activation_key_names = soundboard_entry["activationKeyNames"]

                    if sound_name in self.sound_name_to_json_sound_path_map:
                        print "JSON-DUPE\toverwriting", sound_name, "activation name", self.sound_name_to_activation_keys_map[sound_name], "with", activation_key_names
                    for i in range(len(activation_key_names)):
                        key_name = activation_key_names[i]
                        if key_name in NAME_OVERRIDE_LIST:
                            activation_key_names[i] = NAME_OVERRIDE_LIST[activation_key_names[i]]
                        if key_name not in KEY_NAMES and key_name not in NAME_OVERRIDE_LIST:
                            print "key name", key_name, "not found in list of valid keys. Skipping sound with invalid activation keys", soundboard_entry["file"]
                            raise Exception('')
                    self.sound_name_to_json_sound_path_map[sound_name] = sound_path
                    self.sound_name_to_activation_keys_map[sound_name] = activation_key_names
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
            inner_dict["file"] = sound_path
            inner_dict["activationKeyNames"] = activation_keys
            base_dict["soundboardEntries"].append(inner_dict)

        with open(new_config_file_path, "w") as f:
            f.write(json.dumps(base_dict).replace('{"file"', '\n\t{"file"'))
    
    def _updateUnassignedSoundsMap(self):
        for name, path in self.sound_name_to_folder_sound_path_map.items():
            if name not in self.sound_name_to_activation_keys_map:
                self.unassigned_sound_names_to_paths_map[name] = path
