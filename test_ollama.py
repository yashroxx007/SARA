import requests

r = requests.post("http://localhost:11434/api/generate",
    json={"model": "gemma4:latest", "prompt": "Say hello in one sentence.", "stream": False})

print(r.json()["response"])