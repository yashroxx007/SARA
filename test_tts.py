import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty('voices')

# Set Samantha - index 138
engine.setProperty('voice', voices[138].id)
engine.setProperty('rate', 175)
engine.say("Hello, I am SARA. I am online.")
engine.runAndWait()