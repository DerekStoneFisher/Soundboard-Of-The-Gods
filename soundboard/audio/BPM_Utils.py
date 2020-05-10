# # import wave, array, math, time
# # import numpy, pywt
# # from scipy import signal
#
# class BPM:
#     def __init__(self):
#         self.time_list = []
#         self.avg_bpm = 140 # blindly guess the bpm if we don't know what it is (140 is standard for dubstep)
#
#
#     def update(self):
#         self.time_list.append(time.time())
#
#         if len(self.time_list) > 1:
#             bpm_list = []
#             for i in range(len(self.time_list)-1):
#                 time_diff = self.time_list[i+1] - self.time_list[i]
#                 bpm_list.append(60 / time_diff)
#             avg_bpm = sum(bpm_list)/len(bpm_list)
#             if avg_bpm < 80:
#                 avg_bpm *= 2
#             self.avg_bpm = avg_bpm
#
#     def speedShiftNeededToMatchOtherBpm(self, otherBpm):
#         """
#         :type otherBpm: float
#         """
#         return 1 - (self.avg_bpm / otherBpm)
#
#
#     def restart(self):
#         self.time_list = []
# #
#
#
#
# # credit for bpm detection goes to https://github.com/scaperot
# # code taken from https://github.com/scaperot/the-BPM-detector-python/blob/master/bpm_detection/bpm_detection.py
# def read_wav(filename):
#     #open file, get metadata for audio
#     try:
#         wf = wave.open(filename,'rb')
#     except IOError, e:
#         print e
#         return
#
#     # typ = choose_type( wf.getsampwidth() )
#     nsamps = wf.getnframes();
#     assert(nsamps > 0);
#
#     fs = wf.getframerate()
#     assert(fs > 0)
#
#     # read entire file and make into an array
#     samps = list(array.array('i',wf.readframes(nsamps)))
#     #print 'Read', nsamps,'samples from', filename
#     try:
#         assert(nsamps == len(samps))
#     except AssertionError, e:
#         print  nsamps, "not equal to", len(samps)
#
#     return samps, fs
#
# # print an error when no data can be found
# def no_audio_data():
#     print "No audio data for sample, skipping..."
#     return None, None
#
# # simple peak detection
# def peak_detect(data):
#     max_val = numpy.amax(abs(data))
#     peak_ndx = numpy.where(data==max_val)
#     if len(peak_ndx[0]) == 0: #if nothing found then the max must be negative
#         peak_ndx = numpy.where(data==-max_val)
#     return peak_ndx
#
# def bpm_detector(data,fs):
#     cA = []
#     cD = []
#     correl = []
#     cD_sum = []
#     levels = 4
#     max_decimation = 2**(levels-1);
#     min_ndx = int(60./ 220 * (fs/max_decimation))
#     max_ndx = int(60./ 40 * (fs/max_decimation))
#
#     for loop in range(0,levels):
#         cD = []
#         # 1) DWT
#         if loop == 0:
#             [cA,cD] = pywt.dwt(data,'db4');
#             cD_minlen = len(cD)/max_decimation+1;
#             cD_sum = numpy.zeros(cD_minlen);
#         else:
#             [cA,cD] = pywt.dwt(cA,'db4');
#         # 2) Filter
#         cD = signal.lfilter([0.01],[1 -0.99],cD);
#
#         # 4) Subtractfilename out the mean.
#
#         # 5) Decimate for reconstruction later.
#         cD = abs(cD[::(2**(levels-loop-1))]);
#         cD = cD - numpy.mean(cD);
#         # 6) Recombine the signal before ACF
#         #    essentially, each level I concatenate
#         #    the detail coefs (i.e. the HPF values)
#         #    to the beginning of the array
#         cD_sum = cD[0:cD_minlen] + cD_sum;
#
#     if [b for b in cA if b != 0.0] == []:
#         return no_audio_data()
#     # adding in the approximate data as well...
#     cA = signal.lfilter([0.01],[1 -0.99],cA);
#     cA = abs(cA);
#     cA = cA - numpy.mean(cA);
#     cD_sum = cA[0:cD_minlen] + cD_sum;
#
#     # ACF
#     correl = numpy.correlate(cD_sum,cD_sum,'full')
#
#     midpoint = len(correl) / 2
#     correl_midpoint_tmp = correl[midpoint:]
#     peak_ndx = peak_detect(correl_midpoint_tmp[min_ndx:max_ndx]);
#     if len(peak_ndx) > 1:
#         return no_audio_data()
#
#     peak_ndx_adjusted = peak_ndx[0]+min_ndx;
#     bpm = 60./ peak_ndx_adjusted * (fs/max_decimation)
#     return bpm,correl
#
# def getBpmFromWavFile(filename):
#     window_seconds = 3
#     samps,fs = read_wav(filename)
#
#     data = []
#     nsamps = len(samps)
#     window_samps = int(window_seconds*fs)
#     samps_ndx = 0  #first sample in window_ndx
#     max_window_ndx = nsamps / window_samps
#     bpms = numpy.zeros(max_window_ndx)
#
#     #iterate through all windows
#     for window_ndx in xrange(0,max_window_ndx):
#         #get a new set of samples
#         #print n,":",len(bpms),":",max_window_ndx,":",fs,":",nsamps,":",samps_ndx
#         data = samps[samps_ndx:samps_ndx+window_samps]
#         if not ((len(data) % window_samps) == 0):
#             raise AssertionError( str(len(data) ) )
#
#         bpm, correl_temp = bpm_detector(data,fs)
#         if bpm == None:
#             continue
#         bpms[window_ndx] = bpm
#
#         #iterate at the end of the loop
#         samps_ndx = samps_ndx+window_samps
#
#     bpm = numpy.median(bpms)
#     return bpm
