import time, thread, threading
from Sound import SoundEntry
import Audio_Utils

class PitchController:
    '''
    Spawns threads to modify the pitches of sounds that get passed to its functions
    '''
    oscillate_lock = threading.Lock()
    sounds_being_oscillated = set()

    oscillate_amplitude = 1.0 # (max of oscillation - min of oscillation) / 2
    oscillate_pitch_shift_per_second = 5.0 # how fast the oscillations occur
    # oscillations_per_second = .5
    total_seconds_of_oscillations = 1.0 # how long the sound is oscillated for

    ticks_per_second = 400.0  # around 2ms per tick, otherwise sleeping stops working
    # pitch_shift_per_tick = (2.0 * this.oscillate_amplitude * this.oscillations_per_second) / ticks_per_second
    pitch_shift_per_tick = oscillate_pitch_shift_per_second / ticks_per_second
    tick_duration_seconds = 1.0 / ticks_per_second

    def __init__(self):
        pass

    @staticmethod
    def oscillateSound(sound):
        this = PitchController
        """
        :type sound: SoundEntry
        """
        with this.oscillate_lock:
            # if sound not in this.sounds_being_oscillated:
            this.sounds_being_oscillated.add(sound)
            thread.start_new_thread(this._oscillateSoundThread, (sound,))

    @staticmethod
    def _oscillateSoundThread(sound):
        """
        :type sound: SoundEntry
        """
        this = PitchController
        direction = 1 # switch to -1 when we hit the peak
        curr_wave_height = 0



        single_oscillation_duration = this.oscillate_amplitude*2 / this.oscillate_pitch_shift_per_second
        total_seconds_of_oscillation =  max(this.total_seconds_of_oscillations, single_oscillation_duration)
        ticks_left = total_seconds_of_oscillation * this.ticks_per_second

        start_time = time.time()
        print "ticks_per_second ", this.ticks_per_second
        print "pitch_shift_per_tick ", this.pitch_shift_per_tick
        print "tick_duration_seconds ", this.tick_duration_seconds
        print "ticks_left ", ticks_left


        while ticks_left >= -2:
            cycle_start_time = time.time()
            if direction == 1 and curr_wave_height >= this.oscillate_amplitude/2:
                direction = -1
                print('peak MAX')
            elif direction == -1 and curr_wave_height <= -this.oscillate_amplitude/2:
                direction = 1
                print('peak MIN')
            # print " - curr_wave_height ",  curr_wave_height, "pitch_modifier ", sound.pitch_modifier, "ticks_left ", ticks_left

            # separately add to both
            curr_wave_height += (this.pitch_shift_per_tick * direction)
            sound.pitch_modifier += (this.pitch_shift_per_tick * direction)

            ticks_left -= 1
            time.sleep(this.tick_duration_seconds - (time.time() - cycle_start_time ))

        # it might have ended early or late, so this will clean up
        if curr_wave_height > .4:
            print "WARNING: _oscillateSoundThread ended with curr_wave_height > .4"
        sound.pitch_modifier -= curr_wave_height



        if sound in this.sounds_being_oscillated:
            this.sounds_being_oscillated.remove(sound)
        # print "it took ", time.time()-start_time

    @staticmethod
    def gradualPitchShiftSound(sound, direction):
        this = PitchController
        """
        :type sound: SoundEntry
        """
        thread.start_new_thread(this._gradualPitchShiftSoundThread, (sound,direction))

    @staticmethod
    def _gradualPitchShiftSoundThread(sound, direction):
        this = PitchController
        """
        :type sound: SoundEntry
        """
        ticks_left = 80
        while ticks_left > 0:
            sound.pitch_modifier += .01 * direction
            time.sleep(0.00625)
            ticks_left -= 1




