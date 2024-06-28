import pytest
from server import app, TextRequest
import requests


@pytest.mark.asyncio
async def test_generate_music():
    url = "http://localhost:8009/generate_audio"
    text_request = TextRequest(text="Speak this text")
    response = requests.post(url, json=text_request.dict())
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "audio/mpeg"
    print("status code and headers are correct")
    # Check the audio data
    audio_data = response.content
    assert len(audio_data) > 0
