import time

class PitchController(object):
    '''
    Spawns threads to modify the pitches of sounds that get passed to its functions
    '''
    oscillation_rate = .01
    oscillation_amplitude = 1

    wobble_pause_frequency = 60
    wobble_amplitude = .2

    gradual_pitch_shift_rate = .0025

    @classmethod
    def adjustOscillationRate(cls, direction, amount=.0025):
        cls.oscillation_rate = max(amount, cls.oscillation_rate + amount*direction)
        print "oscillation_rate:", cls.oscillation_rate

    @classmethod
    def adjustOscillationAmplitude(cls, direction, amount=.1):
        cls.oscillation_amplitude = max(amount, cls.oscillation_amplitude + amount*direction)
        print "oscillation_amplitude:", cls.oscillation_amplitude

    @classmethod
    def adjustWobbleAmplitude(cls, direction, amount=.05):
        cls.wobble_amplitude = max(amount, cls.wobble_amplitude + amount*direction)
        print "wobble_amplitude:", cls.wobble_amplitude

    @classmethod
    def adjustWobblePauseFrequency(cls, direction, amount=1):
        cls.wobble_pause_frequency = max(amount, cls.wobble_pause_frequency + amount*direction)
        print "wobble_pause_frequency:", cls.wobble_pause_frequency

    @classmethod
    def genWobble(cls):
        '''
        alternates between a high and low pitch
        e.g. -1, 2, -1, 2, -1, 2
        :return: None
        '''
        direction = 1.0
        pauses_left = cls.wobble_pause_frequency

        # this is a generator will run for as long as it keeps getting called.
        # the caller is responsible for keeping track of how many times they want
        # to call it,
        while True:
            if pauses_left == 0:
                yield cls.wobble_amplitude * direction
                direction = -direction
                pauses_left = cls.wobble_pause_frequency
            else:
                pauses_left -= 1
                yield 0

    @classmethod
    def genOscillate(cls):
        '''
        oscillates like so:
         - e.g. amplitude of 4 and rate of 1 goes:
           0, -1, -2, -1, 0, 1, 2, 1, 0
        :return:
        '''
        direction = 1.0 # switch to -1 when we hit the peak
        curr_wave_height = 0.0

        while True:
            if direction == 1 and curr_wave_height >= cls.oscillation_amplitude/2:
                direction = -1
            elif direction == -1 and curr_wave_height <= -cls.oscillation_amplitude/2:
                direction = 1

            curr_wave_height += cls.oscillation_rate * direction
            yield cls.oscillation_rate * direction

    # @staticmethod
    # def gradualPitchShiftSound(sound, direction):
    #     this = PitchController
    #     """
    #     :type sound: SoundEntry
    #     """
    #     thread.start_new_thread(this._gradualPitchShiftSoundThread, (sound,direction))
    #
    # @staticmethod
    # def _gradualPitchShiftSoundThread(sound, direction):
    #     this = PitchController
    #     """
    #     :type sound: SoundEntry
    #     """
    #     ticks_left = 80
    #     while ticks_left > 0:
    #         sound.pitch_modifier += .01 * direction
    #         time.sleep(0.00625)
    #         ticks_left -= 1




