# mic_test.py
# Simple Raspberry Pi Microphone Test

import sounddevice as sd
import numpy as np

duration = 5  # seconds
sample_rate = 44100

print("Recording... Speak into the microphone")

# Record audio
audio = sd.rec(
    int(duration * sample_rate),
    samplerate=sample_rate,
    channels=1,
    dtype='float32'
)

sd.wait()

print("Recording complete")

# Calculate volume level
volume = np.linalg.norm(audio) * 10

print("Detected Volume Level:", volume)

if volume > 1:
    print("Microphone is WORKING")
else:
    print("No significant sound detected")