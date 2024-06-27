from fastapi import FastAPI, Body
import torch
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
from fastapi.responses import StreamingResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from pydub import AudioSegment
from datetime import datetime
import io

class Song(BaseModel):
    description: str = "upbeat pop rock"
    duration: int | None = 5

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    global model
    model = MusicGen.get_pretrained('facebook/musicgen-melody-large')
    # model = MusicGen.get_pretrained('facebook/musicgen-small')


@app.post("/generate_music")
async def generate_music(song: Song):
    # print("Description is...")
    # print(song.description)
    # print("duration is:")
    # print(song.duration)
    model.set_generation_params(duration=int(song.duration))
    wav = model.generate([song.description], progress=True)
    dt = datetime.now()
    ts = int(dt.timestamp())

    def iterfile(file_path):
        with open(file_path, "rb") as file_like:
            yield from file_like

    for idx, one_wav in enumerate(wav):
        with io.BytesIO() as wav_file:
            filepath = f"samples/{ts}/{idx}"
            audio_write(filepath, one_wav.cpu(), model.sample_rate, strategy="loudness", loudness_compressor=True)
            wav_file.seek(0)
            response = StreamingResponse(iterfile(f"{filepath}.wav"), media_type="audio/wav")
            return response
