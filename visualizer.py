import pyaudio
import sys, pygame
import numpy as np
from scipy.fftpack import fft

# PYGAME SETUP
pygame.init()
size = width, height = 1200, 900
speed = [2, 2]
black = 0, 0, 0

screen = pygame.display.set_mode((width, height))

# AUDIO INPUT SETUP
defaultframes = 512

recorded_frames = []
device_info = {}
useloopback = False

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

numBins = width // 5 #10
amplitudeMult = height / 10
# baseHeight = height / 5
lastCount = [0 for i in range(numBins)]
lastlastCount = [0 for i in range(numBins)]

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                width = 1920
                height = 1080
                numBins = width // 5
                amplitudeMult = height / 10
                lastCount = [0 for i in range(numBins)]
                lastlastCount = [0 for i in range(numBins)]
                screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)

    frame = stream.read(defaultframes)
    data = np.frombuffer(frame, dtype='<i2').reshape(-1, channelcount)
    pdata = list(((a[0] + a[1]) / 2) for a in data)
    fdata = fft(pdata)
    # FFT produces negative values, only get positive
    y = 2 / len(fdata) * np.abs(fdata[0:np.int(len(fdata) / 2)])
    binMembers = [0 for i in range(numBins + 1)]
    for val in y:
        if val <= 0.5:
            continue
        for i in range(1, numBins + 1):
            if val <= 10 ** (0.01 * i):
                if i-2 >= 0:
                    binMembers[i-2] += 0.03
                binMembers[i-1] += 1
                if i <= numBins:
                    binMembers[i] += 0.03
                break

    bgcolor = pygame.Color(0)
    screen.fill(bgcolor)
    for i in range(1, numBins):
        avgNum = (binMembers[i] + lastCount[i] + lastlastCount[i]) / 3
        rect = pygame.Rect(i * width/numBins, (height / 2) - (avgNum * amplitudeMult) / 2
                           , width/numBins, avgNum * amplitudeMult)
        col = pygame.Color(0)
        col.hsla = i * (360 / numBins), 50, 50, 100
        # col.hsla = (avgNum * 30, 50, 50, 100) if avgNum * 30 <= 360 else (360, 50, 50, 100)
        pygame.draw.rect(screen, col, rect)
        lastlastCount[i] = lastCount[i]
        lastCount[i] = avgNum

    pygame.display.flip()