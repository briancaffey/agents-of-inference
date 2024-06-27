# MusicGen

A simple service for generating music using [musicgen from facebookresearch/audiocraft](https://github.com/facebookresearch/audiocraft/blob/main/docs/MUSICGEN.md).

## Install dependencies

```
pip install -r requirements.txt
pip install torch==2.1.0+cu121 torchaudio --index-url https://download.pytorch.org/whl/cu121
```

## Start the server

```
fastapi dev server.py
```

## Test

```
pytest test_musicgen.py
```

## Usage

```python
import requests
import datetime

url = "http://localhost:8000/generate_music"

description = "Upbeat pop rock"  # Replace with your song description

response = requests.post(url, json={"description": description, "duration": 10})


if response.status_code == 200:
    filename = f"songs/{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.wav"
    with open(filename, "wb") as f:
        f.write(response.content)
    print("Music generated and saved wav")
else:
    print("Failed to generate music:", response.status_code, response.text)
```
