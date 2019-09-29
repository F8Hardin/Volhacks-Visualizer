import pyaudio
import wave
import os
import numpy as np
from scipy.fftpack import fft
from matplotlib import pyplot as plt
from matplotlib.ticker import ScalarFormatter
from scipy.interpolate import make_interp_spline, BSpline

defaultframes = 256

recorded_frames = []
device_info = {}
useloopback = False

# Set up the plot/axes
fig, ax = plt.subplots(1, figsize=(15, 7))

# Use module
p = pyaudio.PyAudio()

# Set default to first in list or ask Windows
try:
    default_device_index = p.get_default_input_device_info()
except IOError:
    default_device_index = -1

# Select Device
print("Available devices:\n")
for i in range(0, p.get_device_count()):
    info = p.get_device_info_by_index(i)
    print(str(info["index"]) + ": \t %s \n \t %s \n" % (
        info["name"], p.get_host_api_info_by_index(info["hostApi"])["name"]))

    if default_device_index == -1:
        default_device_index = info["index"]

# Handle no devices available
if default_device_index == -1:
    print("No device available. Quitting.")
    exit()

# Get input or default
device_id = int(input("Choose device [" + str(default_device_index) + "]: ") or default_device_index)
print("")

# Get device info
try:
    device_info = p.get_device_info_by_index(device_id)
except IOError:
    device_info = p.get_device_info_by_index(default_device_index)
    print("Selection not available, using default.")

# Choose between loopback or standard mode
is_input = device_info["maxInputChannels"] > 0
is_wasapi = (p.get_host_api_info_by_index(device_info["hostApi"])["name"]).find("WASAPI") != -1
if is_input:
    print("Selection is input using standard mode.\n")
else:
    if is_wasapi:
        useloopback = True;
        print("Selection is output. Using loopback mode.\n")
    else:
        print("Selection is input and does not support loopback mode. Quitting.\n")
        exit()

# Open stream
channelcount = device_info["maxInputChannels"] if (
        device_info["maxOutputChannels"] < device_info["maxInputChannels"]) else device_info["maxOutputChannels"]
stream = p.open(format=pyaudio.paInt16,
                channels=channelcount,
                rate=int(device_info["defaultSampleRate"]),
                input=True,
                frames_per_buffer=defaultframes,
                input_device_index=device_info["index"],
                as_loopback=useloopback)

# Start Recording
print("Starting...")
print("Channel Count: " + str(channelcount))

# variable for plotting
x = np.arange(0, defaultframes)

# create a line object with random data
line, = ax.semilogx(x, np.random.rand(defaultframes), '-', lw=7)

# basic formatting for the axes
ax.set_title('Audio Spectrum Analysis')
ax.set_xlabel('frequency (daHz)')
ax.set_ylabel('intensity')
# ax.set_autoscale_on(True)
# ax.autoscale_view(True, False, False)
ax.set_xscale('log')
ax.set_xticks([2, 6, 25, 50, 200, 400, 600, 2000])
ax.get_xaxis().set_major_formatter(ScalarFormatter())

# show the plot
plt.xlim([2, defaultframes / 2])
plt.ylim([0, 8192])
plt.show(block=False)

while True:
    frame = stream.read(defaultframes)
    data = np.frombuffer(frame, dtype='<i2').reshape(-1, channelcount)
    pdata = list(((a[0] + a[1]) / 2) for a in data)
    fdata = fft(pdata)
    # FFT produces negative values, only get positive
    y = 2 / len(fdata) * np.abs(fdata[0:np.int(len(fdata) / 2)])

    xnew = np.linspace(0, len(y), 350)
    smooth = make_interp_spline(np.arange(0, len(y)), y, k=3)
    ysmooth = smooth(xnew)

    try:
        yavg = np.mean([ysmooth, lasty], axis=0)
        line.set_data(xnew, yavg)
    except NameError:
        # line.set_data(np.arange(0, len(y)), y)
        line.set_data(xnew, ysmooth)

    ax.relim()
    ax.autoscale_view(True, False, False)
    fig.canvas.draw()
    fig.canvas.flush_events()

    lasty = ysmooth
