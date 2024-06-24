import io
import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from PIL import Image
import torch
from diffusers import StableVideoDiffusionPipeline
from diffusers.utils import load_image, export_to_video

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
    print(f"Uploaded file content type: {file.content_type}")
    if file.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(status_code=400, detail="Invalid image format")
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image.verify()  # Verify that it is, in fact, an image
        return Image.open(io.BytesIO(contents))  # Reopen after verification
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="Invalid image content")

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
        video_frames = pipe(image, decode_chunk_size=1, generator=generator, motion_bucket_id=180, noise_aug_strength=0.1)

        print("processing frames...")
        frames = video_frames.frames[0]
        print("frames processed")
        # Save the generated video
        video_path = "generated.mp4"
        print("export_to_video")
        export_to_video(frames, video_path, fps=7)
        print("return FileResponse")
        return FileResponse(video_path, media_type="video/mp4", filename="generated.mp4")
    except HTTPException as e:
        raise e  # Re-raise HTTP exceptions as is
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(video_path):
            # os.remove(video_path)
            pass
