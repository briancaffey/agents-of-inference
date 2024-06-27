import datetime

import torchaudio
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write

model = MusicGen.get_pretrained('facebook/musicgen-melody-large')
model.set_generation_params(duration=30)
wav = model.generate_unconditional(1)

descriptions = [
    "suspensful action movie scene intense"
]
wav = model.generate(descriptions, progress=True)

# save samples in different folders
dt = datetime.datetime.now()
ts = int(dt.timestamp())

for idx, one_wav in enumerate(wav):
    print(f"Creating audio for {idx}")
    # Will save under samples/{ts}/{idx}.wav, with loudness normalization at -14 db LUFS.
    audio_write(f'samples/{ts}/{idx}', one_wav.cpu(), model.sample_rate, strategy="loudness", loudness_compressor=True)
