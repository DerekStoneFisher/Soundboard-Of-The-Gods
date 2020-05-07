# Soundboard of the Gods

"Soundboard of the Gods" is the ultimate featured packed, high performance soundboard your life needs.

## High Performance
All the sounds are loaded into memory before being played, so sounds can be modulated and remixed *as they are played*. This also means playing sounds and executing commands on them is incredibly fast and responsive. And thanks to a dynamically scaled pool of shared output streams, you can choose to play and remix any number of sounds simultaneously

## Features
This soundboard is all about real-time sound manipulation and feature overload
- Record and instantly play back sounds, or save them to the soundboard for later
- Reverse sounds and songs half-way through, then reverse them again back to normal
- Modulate the pitch of sounds in a variety of ways **as you play them**
  -  Increase or decrease the pitch with a single button
  -  Activate one of the "oscillation" modes to add a crazy wavy effect to the sound

 Use the more advanced "DJ" features to remix songs and sounds in real time
  - Mark the current location of a sound being played, then jump back to that location with the press of a button
  - Activate "Piano Mode" and play the sound like a piano by using the keys on the keyboard
  - Use the **Automatic or Manual BPM detection** features to synchronize multiple songs and create your own DJ set

   Let the soundboard handle the setup for you
   - Automated input/output device detection
   - Simultaneous output to both your speakers and virtual audio cable so you and your friends can hear your soundboard
    - Automatic decibel normalization is done across all sounds so they always have the same volume

## Technology
- pyaudio used for sound  recording and playing
- pydub used for breaking WAVs into editable chunks
- pyHook used for capturing key events
- tkinter used for current UI