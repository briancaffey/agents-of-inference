import os

import requests
import datetime

MUSICGEN_SERVICE_HOST = os.environ.get("MUSICGEN_SERVICE_HOST", "192.168.5.96")
MUSICGEN_SERVICE_PORT = os.environ.get("MUSICGEN_SERVICE_PORT", "8011")

MUSICGEN_SERVICE_PORT = "8011"

url = f"http://{MUSICGEN_SERVICE_HOST}:{MUSICGEN_SERVICE_PORT}/generate_music"
print("URL for musicgen ", url)
# description = "Acoustic guitars, banjos, and fiddle-like instruments create a sense of rustic, earthy connection to the natural world and its migrations."
description = """
Somber tone Acoustic guitars, banjos, and fiddle-like instruments
"""

# description = """
# funk music
# """
description = "Classical music with happy upbeat melody and synth wave"  # Replace with your song description
description = "1980s happy party music relaxed chill"

response = requests.post(url, json={"description": description, "duration": 30})

print(f"description: {description}")


if response.status_code == 200:
    filename = f"musicgen/songs/{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.wav"
    with open(filename, "wb") as f:
        f.write(response.content)
    print("Music generated and saved wav")
else:
    print("Failed to generate music:", response.status_code, response.text)

