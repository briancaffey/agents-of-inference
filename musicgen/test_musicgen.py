import os
import pytest
from server import app, Song
import requests

MUSICGEN_SERVICE_HOST = os.environ.get("MUSICGEN_SERVICE_HOST", "192.168.1.123")
MUSICGEN_SERVICE_PORT = os.environ.get("MUSICGEN_SERVICE_PORT", "192.168.1.123")

@pytest.mark.asyncio
async def test_generate_music():
    url = f"http://{MUSICGEN_SERVICE_HOST}:{MUSICGEN_SERVICE_PORT}/generate_music"
    song = Song(description="Test Song", duration=5)  # assume Song class has constructor
    response = requests.post(url, json=song.dict())
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "audio/wav"
    print("status code and headers are correct")
    # Check the audio data
    audio_data = response.content
    # You can write a test to verify the audio data (e.g., its length, samples, etc.)
    # For simplicity, let's assume the audio data is valid
    assert len(audio_data) > 0
