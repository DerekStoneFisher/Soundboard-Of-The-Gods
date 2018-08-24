from tkinter import *
import Sound
import thread
import time

window = Tk()
window.title("Soundboard")
window.geometry("640x480")

soundCollection = Sound.SoundCollection()

def play(sound_entry):
    print "playing", sound_entry.path_to_sound
    if not sound_entry.is_playing: # start playing it if it not playing
        thread.start_new_thread(sound_entry.play, tuple())
    else: # stop playing it if hold_to_play is off and the key was let go
        thread.start_new_thread(sound_entry.stop, tuple())
        counter = 0
        while sound_entry.stream_in_use and counter < 1000: # wait for the sound_entry to finish outputting its current chunk to the stream if it is in the middle of doing so
            time.sleep(.001)
            counter += 1
        thread.start_new_thread(sound_entry.play, tuple())


i = 0
for k,v in soundCollection.key_bind_map.iteritems():
    button = Button(window, text=v.path_to_sound, command=v.playMultiThreaded)
    button.grid(column=i, row=0)
    i += 1

button = Button(window, text="stopAllSounds()", command=soundCollection.stopAllSounds)
button.grid(column=0, row=1)

button = Button(window, text="addNewSound()", command=soundCollection.add)




window.mainloop()


