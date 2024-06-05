from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from typing import Optional
import torch
from diffusers import StableVideoDiffusionPipeline
from diffusers.utils import load_image, export_to_video
from PIL import Image
import io
import os

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    global pipe
    device = "cuda" if torch.cuda.is_available() else "cpu"

    pipe = StableVideoDiffusionPipeline.from_pretrained(
        "stabilityai/stable-video-diffusion-img2vid-xt", torch_dtype=torch.float16, variant="fp16"
    ).to(device)
    pipe.enable_model_cpu_offload()

async def validate_image(file: UploadFile) -> Image.Image:
    if file.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(status_code=400, detail="Invalid image format")
    contents = await file.read()
    return Image.open(io.BytesIO(contents))

@app.post("/api/img2vid")
async def convert_img_to_vid(image_file: UploadFile = File(...)):
    try:
        # Validate the uploaded image
        image = await validate_image(image_file)
        
        # Resize the image
        image = image.resize((1024, 576))
        
        # Generate frames using SVD
        generator = torch.manual_seed(42)
        print("processing video_frames")
        video_frames = pipe(image, decode_chunk_size=2, generator=generator, motion_bucket_id=180, noise_aug_strength=0.1)

        print("processing frames...")
        frames = video_frames.frames[0]

        # Save the generated video
        video_path = "generated.mp4"

        export_to_video(frames, video_path, fps=7)
        return FileResponse(video_path, media_type="video/mp4", filename="generated.mp4")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(video_path):
            # os.remove(video_path)
            pass
