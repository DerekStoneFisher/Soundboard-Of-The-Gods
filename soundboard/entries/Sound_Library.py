import os, json
from collections import OrderedDict
from soundboard.keys.Key_Utils import keyNamesAreValid

class SoundLibrary:
    def __init__(self, soundboard_json_config_path, soundboard_sounds_base_directory):
        '''
        The Sound Library contains all of the sounds paths and activation keys of the sounds in the Board JSON file
        It can add sounds to the JSON file, edit activation keys for sounds in the JSON file, and delete sounds from the JSON file
        :param soundboard_json_config_path: str
        :param soundboard_sounds_base_directory: str
        '''
        self._soundboard_json_config_path = soundboard_json_config_path
        self._soundboard_sounds_base_directory = soundboard_sounds_base_directory

        self.sound_paths = dict()  # name string -> path string
        self.sound_activation_keys = OrderedDict()  # name string -> list of key name strings. Maintains order of sounds in json.
        # self._missing_sound_names = [] # sounds that weren't found in the soundbaord folder
        # self._invalid_activation_keys = OrderedDict()

        self._refreshSoundPathsAndActivationKeys()

    def _refreshSoundPathsAndActivationKeys(self):
        '''
        Updates self.sound_paths and self.sound_activation_keys by:
        1. Recursively traverse soundboard base directory and save the file names and paths of all WAV files.
        2. For each sound in the soundboard config json, save its activation keys if the sound
           exists within the soundboard sounds folder and if the activation keys are valid.
        :return: None
        '''
        for directory_path, directory_name, filenames in os.walk(self._soundboard_sounds_base_directory):
            for filename in filenames:
                if filename.endswith(".wav"):
                    self.sound_paths[filename] = os.path.join(directory_path, filename).replace('\\', '/')

        with open(self._soundboard_json_config_path) as config_file:
            config_object = json.load(config_file)
            soundboard_entries = config_object['soundsWithKeys']
            for soundboard_entry in soundboard_entries:
                sound_name = soundboard_entry['name']
                activation_key_names = soundboard_entry['activationKeys']

                if sound_name not in self.sound_paths:
                    print "sound", sound_name, "not found."
                    continue
                elif not keyNamesAreValid(activation_key_names):
                    print "sound", sound_name, "has invalid activation keys ", activation_key_names
                    continue
                else:
                    self.sound_activation_keys[sound_name] = activation_key_names

    # def getMapOfPathsToKeyBinds(self):
    #     '''
    #     Returns a map of sound paths to their activation key names
    #     :return: dict(str: list(str))
    #     '''
    #     binds = OrderedDict()
    #     for sound_name, activation_keys in self.sound_activation_keys.items():
    #         binds[self.sound_paths[sound_name]] = activation_keys
    #     return binds


    def getKeyBindMap(self):
        '''
        Returns a map of sound activation keys to sound paths
        :return: dict(frozenset(str): str)
        '''
        binds = OrderedDict()
        for sound_name, activation_keys in self.sound_activation_keys.items():
            binds[frozenset(activation_keys)] = self.sound_paths[sound_name]
        return binds

    def saveChanges(self):
        '''
        Saves changes to the same soundboard json file that was passed in
        :return: None
        '''
        config_object = {'soundsWithKeys': []}
        for sound_name, activation_keys in self.sound_activation_keys.items():
            entry = OrderedDict([('name', sound_name), ('activationKeys', activation_keys)])
            config_object['soundsWithKeys'].append(entry)
        with open(self._soundboard_json_config_path, 'w') as json_file:
            json_file.write(json.dumps(config_object, json_file).replace('{"file"', '\n\t{"file"'))

    def deleteByName(self, sound_name, save_changes=True):
        '''
        Deletes the sound by name, saving changes to the json by default
        :param sound_name: str
        :param save_changes: bool
        :return: None
        '''
        if sound_name in self.sound_activation_keys:
            del self.sound_activation_keys[sound_name]
            print "DEBUG: deleted sound", sound_name
            if save_changes:
                self.saveChanges()
        else:
            print "DEBUG: cannot delete sound", sound_name, "because it does not exist"

    def add(self, path_to_sound, activation_keys, save_changes=True):
        '''
        :param path_to_sound: str
        :param activation_keys: list(str)
        :param save_changes: bool
        :return: None
        '''
        if self._soundboard_sounds_base_directory not in path_to_sound:
            print "cannot add sound", path_to_sound, "because it is not in soundboard sounds base directory", self._soundboard_sounds_base_directory
            return

        sound_name = os.path.basename(path_to_sound)
        self.sound_activation_keys[sound_name] = activation_keys
        self.sound_paths[sound_name] = path_to_sound
        if save_changes:
            self.saveChanges()

    def getPathsOfSoundsWithoutActivationKeys(self):
        '''
        Returns the paths of all sounds that exist in the soundboard folder but have no activation keys bound to them
        :return: list(str)
        '''
        names_without_activation_keys = [name for name in self.sound_activation_keys.keys() if
                                         name not in self.sound_paths.keys()]
        return [self.sound_paths[name] for name in names_without_activation_keys]


