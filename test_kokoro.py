from kokoro_onnx import Kokoro
import sounddevice as sd

kokoro = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
samples, sample_rate = kokoro.create("Hello, I am SARAH. I am online.", voice="af_sarah", speed=1.0, lang="en-us")
sd.play(samples, sample_rate)
sd.wait()