import subprocess
import base64
import os
import tempfile


def get_screen_context(question: str = "What is on the screen?") -> str:
    """Take a screenshot and ask Claude vision what's on it."""
    import anthropic
    from dotenv import load_dotenv
    load_dotenv()

    # Capture screenshot to a temp file
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()

    result = subprocess.run(
        ["screencapture", "-x", "-t", "png", tmp.name],
        capture_output=True
    )
    if result.returncode != 0:
        return "Couldn't take a screenshot."

    try:
        with open(tmp.name, "rb") as f:
            img_b64 = base64.standard_b64encode(f.read()).decode()
    finally:
        os.unlink(tmp.name)

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img_b64
                    }
                },
                {
                    "type": "text",
                    "text": f"{question} Answer in 1-3 short sentences suitable for speaking aloud. No markdown."
                }
            ]
        }]
    )
    return response.content[0].text.strip()
