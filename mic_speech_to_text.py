# speech_to_text.py
# Convert microphone speech to text on Raspberry Pi

import speech_recognition as sr

# Create recognizer
recognizer = sr.Recognizer()

# Use microphone
with sr.Microphone() as source:

    print("Adjusting for background noise...")
    recognizer.adjust_for_ambient_noise(source, duration=2)

    print("Speak something:")

    # Listen from mic
    audio = recognizer.listen(source)

    print("Processing...")

    try:
        # Convert speech to text
        text = recognizer.recognize_google(audio)

        print("You said:")
        print(text)

    except sr.UnknownValueError:
        print("Could not understand audio")

    except sr.RequestError as e:
        print("Could not request results")
        print(e)