# Note: Modified for Terraria
# Ok, I could have been a lot more clear
# about what was going on. I'm kind of lost lol	

from pynput.mouse import Button, Controller

# keyboard.press('a')
# keyboard.release('a')

import pyaudio
import sys
import numpy as np
import sounddevice as sd
from scipy import signal
import scipy.io.wavfile as scipyread
import time
import matplotlib.pyplot as plt


# As stated elsewhere, there are three buffers.
# Each run, we join two of them and continue to
# fill the third. 
# CHUNK is number of samples per chunk
# CHUNKS_PER_BUF will dictate number of chunks per 
# individual buffer. 
# PADDED_SIZE is the size that the sample and 
# joined chunks are padded to 
CHUNK = 2048
CHUNKS_PER_BUF = 2
PADDED_SIZE = 2**14
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 120
KEEP_AUDIO = 0



if RECORD_SECONDS == 0:
	KEEP_AUDIO = 0

buf = [[],[],[]]
buf_sel = 0
buf_done = 0

done = 0

mouse = Controller()

def cast():
	global mouse
	mouse.press(Button.left)
	time.sleep(0.1)
	mouse.release(Button.left)
	time.sleep(0.5)


def retreive():
	global mouse
	mouse.press(Button.left)
	time.sleep(0.1)
	mouse.release(Button.left)
	time.sleep(0.5)

# This executes every time a chunk has been filled
def callback(in_data, frame_count, time_info, status):
	global buf
	global buf_sel
	global buf_done

	buf[buf_sel].append(in_data)

	if buf_done == 1:
		print('O!')

	if len(buf[buf_sel]) >= CHUNKS_PER_BUF:
		buf_sel = 1 + buf_sel
		if buf_sel == 3:
			buf_sel = 0
		buf_done = 1

	return (bytes(0x00), pyaudio.paContinue)



b = scipyread.read('bloop.wav')[1]
# b = np.array(signal.decimate(b, 2, zero_phase=True, ftype='iir'), dtype=np.int16)
bz = np.pad(b, (0,PADDED_SIZE-b.size), mode='constant', constant_values=0)
bft = np.fft.rfft(bz)
nbft = bft / np.linalg.norm(bft)
cbft = np.conj(nbft)
start_time = time.time()

# Here's the logic for a look-up table (LUT)
# When buf_sel = 0, 
# buf2 = buf[1] + buf[2]
# Remove buf[1]
# So on and so forth.
buf_lut = [[1,2],[2,0],[0,1]]


print ("* Starting. Throw your line into the water")

# TODO: use sd.query_devices() to find CABLE Output and use that as the device index
p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
				channels=CHANNELS, 
				rate=RATE, 
				input=True,
				output=False,
				stream_callback=callback,
				frames_per_buffer=CHUNK,
				input_device_index=3
				)

stream.start_stream()

rec_data = []
alt = 0

try:
	while done == 0:

		# This loop executes twice a second
		if buf_done == 1:
			buf2 = buf[buf_lut[buf_sel][0]][0:CHUNKS_PER_BUF] + buf[buf_lut[buf_sel][1]][0:CHUNKS_PER_BUF]
			buf[buf_lut[buf_sel][0]] = []

			a = np.frombuffer(b''.join(buf2), np.int16)
			if(len(a) > (CHUNK * CHUNKS_PER_BUF)):

				if KEEP_AUDIO == 1:
					# We are doing 3 buffers, each call overlapping two buffers.
					if alt == 1:
						alt = 0
						rec_data.append(a)
					else:
						alt = 1

				ap = np.pad(a, (0, PADDED_SIZE-a.size), mode='constant', constant_values=0)
				aft = np.fft.rfft(ap)
				naft = aft / np.linalg.norm(aft)
				c = np.fft.irfft(naft*cbft)

				print(f'[{time.time() - start_time},{max(np.abs(c))*10**7}],')

				if sum(a==0) > 7000:
					print('I don\'t hear anything')
					done = 1

				if max(abs(c))*10**7 > 900:
					stream.stop_stream()
					print('fish')
					retreive()
					cast()
					buf = [[],[],[]]
					buf_done = 0
					stream.start_stream()

			if RECORD_SECONDS != 0:
				if (time.time() - start_time) > RECORD_SECONDS:
					done = 1

			buf_done = 0
			# stream.start_stream()
		time.sleep(0.001)
	print ("* done")
	stream.stop_stream()
	stream.close()
	p.terminate()

	if KEEP_AUDIO == 1:
		scipyread.write('output.wav', 44100, np.frombuffer(b''.join(rec_data), np.int16))

except :
	print('* closing')
	stream.stop_stream()
	stream.close()
	p.terminate()

