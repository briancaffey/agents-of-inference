from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
from gradio_client import Client
import datetime
import os
import shutil
import uvicorn
from fastapi.responses import FileResponse

app = FastAPI()

CHATTTS_URL = "http://192.168.5.96:8080/"
client = Client(CHATTTS_URL)

class TextRequest(BaseModel):
    text: str

@app.post("/generate_audio")
def generate_audio(request: TextRequest):
    try:
        result = client.predict(
            text=request.text,
            temperature=0.3,
            top_P=0.7,
            top_K=20,
            audio_seed_input=2,
            text_seed_input=42,
            refine_text_flag=True,
            api_name="/generate_audio"
        )

        # Extracting the audio file path from the result
        audio_file_info = result[0]
        audio_file_path = audio_file_info

        # Downloading the audio file
        temp_dir = "/".join(audio_file_path.split("\\")[:-1])
        audio_filename = audio_file_path.split("\\")[-1]

        # Create a destination folder if not exists
        dt = datetime.datetime.now()
        ts = int(dt.timestamp())
        destination_folder = f"./{ts}/downloads"
        os.makedirs(destination_folder, exist_ok=True)

        # Move the downloaded audio file to the downloads folder
        final_audio_path = os.path.join(destination_folder, audio_filename)
        shutil.move(os.path.join(temp_dir, audio_filename), final_audio_path)

        return FileResponse(final_audio_path, media_type='audio/mpeg', filename=audio_filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8009)
