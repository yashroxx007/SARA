import whisper
import sounddevice as sd
import numpy as np

model = whisper.load_model("base")
print("Model loaded. Speak for 5 seconds...")
audio = sd.rec(int(5 * 16000), samplerate=16000, channels=1, dtype='float32')
sd.wait()
print("Processing...")
result = model.transcribe(audio.flatten())
print("You said:", result["text"])