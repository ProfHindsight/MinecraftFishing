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

chunk = 8192
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 120

buf = [[],[],[]]
buf_sel = 0
buf_done = 0

done = 0

mouse = Controller()

def cast():
	global mouse
	mouse.press(Button.right)
	time.sleep(0.1)
	mouse.release(Button.right)
	time.sleep(0.5)


def retreive():
	global mouse
	mouse.press(Button.right)
	time.sleep(0.1)
	mouse.release(Button.right)
	time.sleep(0.5)

# This executes every time a chunk has been filled
def callback(in_data, frame_count, time_info, status):
	global buf
	global buf_sel
	global buf_done

	buf[buf_sel].append(in_data)

	if buf_done == 1:
		print('O!')

	if len(buf[buf_sel]) >= 4:
		buf_sel = 1 + buf_sel
		if buf_sel == 3:
			buf_sel = 0
		buf_done = 1

	return (bytes(0x00), pyaudio.paContinue)



b = scipyread.read('fish.wav')[1]
# b = np.array(signal.decimate(b, 2, zero_phase=True, ftype='iir'), dtype=np.int16)
bz = np.pad(b, (0,2**17-b.size), mode='constant', constant_values=0)
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

p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
				channels=CHANNELS, 
				rate=RATE, 
				input=True,
				output=False,
				stream_callback=callback,
				frames_per_buffer=chunk,
				input_device_index=2
				)

stream.start_stream()

rec_data = []

try:
	while done == 0:

		# This loop executes twice a second
		if buf_done == 1:
			buf2 = buf[buf_lut[buf_sel][0]][0:4] + buf[buf_lut[buf_sel][1]][0:4]
			buf[buf_lut[buf_sel][0]] = []

			a = np.frombuffer(b''.join(buf2), np.int16)
			rec_data.append(a)
			ap = np.pad(a, (0, 2**17-a.size), mode='constant', constant_values=0)
			aft = np.fft.rfft(ap)
			naft = aft / np.linalg.norm(aft)
			c = np.fft.irfft(naft*cbft)

			print(f'[{time.time() - start_time},{max(np.abs(c))*10**7}],')

			if sum(a==0) > 40000:
				print('I don\'t hear anything')
				done = 1

			if max(abs(c))*10**7 > 50:
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
			stream.start_stream()
		time.sleep(0.001)
	print ("* done")
	stream.stop_stream()
	stream.close()
	p.terminate()

except :
	print('* closing')
	stream.stop_stream()
	stream.close()
	p.terminate()

