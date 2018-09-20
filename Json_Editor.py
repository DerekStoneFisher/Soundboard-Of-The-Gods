import json, os
from collections import OrderedDict
# SOUNDBOARD_BASE_DIRECTORY = "C:/Users/Admin/Desktop/Soundboard"
SOUNDBOARD_BASE_DIRECTORY = "D:/DerekProjects/Python_Script_Stuff/Audio_Recorder/sounds/pretend soundboard folder"
SOUNDBOARD_JSON_FILE = "D:/DerekProjects/Python_Script_Stuff/Audio_Recorder/sounds/pretend soundboard folder/pretend soundboard file.json"
SOUNDBOARD_JSON_FILE_EDITED = "D:/DerekProjects/Python_Script_Stuff/Audio_Recorder/sounds/pretend soundboard folder/pretend soundboard file_edited.json"




sound_name_to_folder_sound_path_map = OrderedDict()
sound_name_to_json_sound_path_map = OrderedDict()
sound_name_to_activation_keys_map = OrderedDict()



def _populateSoundMapFromSoundboardFolder(soundboard_base_directory):
    for directory_path, directory_name, filenames in os.walk(soundboard_base_directory):
        for filename in filenames:
            if filename.endswith(".wav"):
                sound_path = (directory_path + "/" + filename).replace("\\", "/")
                if filename in sound_name_to_folder_sound_path_map:
                    print "FILE-DUPE\toverwriting", filename, "sound_path of\t", sound_name_to_folder_sound_path_map[filename], "\twith\t", sound_path
                sound_name_to_folder_sound_path_map[filename] = sound_path



def _populateSoundMapFromJson(config_file_path):
    with open(config_file_path) as config_file:
        config_object = json.load(config_file)
        soundboard_entries = config_object["soundboardEntries"]
        for soundboard_entry in soundboard_entries:
            try:
                sound_path = soundboard_entry["file"].replace("\\", "/")
                sound_name = os.path.basename(sound_path)
                activation_key_codes = soundboard_entry["activationKeysNumbers"]

                if sound_name in sound_name_to_json_sound_path_map:
                    print "JSON-DUPE\toverwriting", sound_name, "activation code", sound_name_to_activation_keys_map[sound_name], "with", activation_key_codes
                sound_name_to_json_sound_path_map[sound_name] = sound_path
                sound_name_to_activation_keys_map[sound_name] = activation_key_codes
            except:
                print "failed to ingest", soundboard_entry["file"]


def _updateJsonSoundPathMapWithActualSoundPathMap():
    for sound_name, json_sound_path in sound_name_to_json_sound_path_map.items():
        activation_keys = sound_name_to_activation_keys_map[sound_name]
        if not os.path.exists(json_sound_path):
            if sound_name in sound_name_to_folder_sound_path_map:
                new_sound_path = sound_name_to_folder_sound_path_map[sound_name]
                print "MOVED    \t", sound_name, "does not exist in the json specified location of\t", json_sound_path, "\tso it is being changed to\t", new_sound_path, "\twith activation keys", activation_keys
                sound_name_to_json_sound_path_map[sound_name] = new_sound_path
            else:
                print "NOT-FOUND\t", sound_name, "does not exist in the soundboard directory. The path specified by the json file is", json_sound_path
        else:
            print "UNCHANGED\t", sound_name, "at", json_sound_path

def _updateJsonWithNewFileLocations(new_config_file_path):
    base_dict = dict()
    base_dict["soundboardEntries"] = []

    for sound_name, sound_path in sound_name_to_json_sound_path_map.items():
        activation_keys = sound_name_to_activation_keys_map[sound_name]
        inner_dict = OrderedDict()
        inner_dict["file"] = sound_path.replace("/", "\\")
        inner_dict["activationKeysNumbers"] = activation_keys
        base_dict["soundboardEntries"].append(inner_dict)

    with open(new_config_file_path, "w") as f:
        f.write(json.dumps(base_dict).replace('{"file"', '\n\t{"file"'))

def runJsonUpdateRoutine(json_config_file_path, json_config_new_file_path, soundboard_folder_path):
    _populateSoundMapFromSoundboardFolder(soundboard_folder_path)
    _populateSoundMapFromJson(json_config_file_path)
    _updateJsonSoundPathMapWithActualSoundPathMap()
    _updateJsonWithNewFileLocations(json_config_new_file_path)



if __name__ == "__main__":
    runJsonUpdateRoutine(SOUNDBOARD_JSON_FILE, SOUNDBOARD_JSON_FILE_EDITED, SOUNDBOARD_BASE_DIRECTORY)