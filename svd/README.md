# SVD

This is a simple service that takes an image and returns a video using Stable Video Diffusion and diffusers.
This has only been tested on Windows 11 with an NVIDIA GeForce RTX 4090 GPU.


## Install

Create a virtual environment with python3.10

```
python3.10.exe -m venv .venv
```

Run the server:

```bash
uvicorn.exe main:app --host 0.0.0.0 --port 8000
```

The FastAPI service accepts POST requests to `/api/img2vid`

```bash
curl -X POST "http://192.168.5.96:8000/api/img2vid" -H "accept: application/json" -H "Content-Type: multipart/form-data" -F "image_file=@image.png"
```

The `stable_video_diffusion_agent` function makes requests to this endpoint to generate short videos from images.