"""
This workflow generates an mp4 video from a 1024x576 image
- It uses TensorRT to generate the video in seconds

For reference: https://github.com/comfyanonymous/ComfyUI_TensorRT
"""


import io
import json
import random
import uuid
import urllib.request
import urllib.parse

import websocket
from PIL import Image
import requests
from diffusers.utils import export_to_video

from .utils import get_images


server_address = "192.168.5.96:8188"
client_id = str(uuid.uuid4())

# Similar to the example workflow show here:
# https://github.com/comfyanonymous/ComfyUI_TensorRT/tree/master?tab=readme-ov-file#common-issueslimitations
PROMPT_TEXT = """{
  "1": {
    "inputs": {
      "ckpt_name": "svd.safetensors"
    },
    "class_type": "ImageOnlyCheckpointLoader",
    "_meta": {
      "title": "Image Only Checkpoint Loader (img2vid model)"
    }
  },
  "2": {
    "inputs": {
      "min_cfg": 1,
      "model": [
        "15",
        0
      ]
    },
    "class_type": "VideoLinearCFGGuidance",
    "_meta": {
      "title": "VideoLinearCFGGuidance"
    }
  },
  "3": {
    "inputs": {
      "width": 1024,
      "height": 576,
      "video_frames": 28,
      "motion_bucket_id": 90,
      "fps": 7,
      "augmentation_level": 0.7,
      "clip_vision": [
        "1",
        1
      ],
      "init_image": [
        "7",
        0
      ],
      "vae": [
        "1",
        2
      ]
    },
    "class_type": "SVD_img2vid_Conditioning",
    "_meta": {
      "title": "SVD_img2vid_Conditioning"
    }
  },
  "4": {
    "inputs": {
      "seed": 1036987423776223,
      "steps": 20,
      "cfg": 2.5,
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 1,
      "model": [
        "2",
        0
      ],
      "positive": [
        "3",
        0
      ],
      "negative": [
        "3",
        1
      ],
      "latent_image": [
        "3",
        2
      ]
    },
    "class_type": "KSampler",
    "_meta": {
      "title": "KSampler"
    }
  },
  "5": {
    "inputs": {
      "samples": [
        "4",
        0
      ],
      "vae": [
        "1",
        2
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "6": {
    "inputs": {
      "frame_rate": 7,
      "loop_count": 0,
      "filename_prefix": "AnimateDiff",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 1,
      "save_metadata": true,
      "pingpong": false,
      "save_output": true,
      "images": [
        "5",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine ????????"
    }
  },
  "7": {
    "inputs": {
      "image": "replace_me.png",
      "upload": "image"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "14": {
    "inputs": {
      "images": [
        "5",
        0
      ]
    },
    "class_type": "PreviewImage",
    "_meta": {
      "title": "Preview Image"
    }
  },
  "15": {
    "inputs": {
      "unet_name": "ComfyUI_DYN_SVD_XT_$dyn-b-28-28-28-h-576-576-576-w-1024-1024-1024_00001_.engine",
      "model_type": "svd"
    },
    "class_type": "TensorRTLoader",
    "_meta": {
      "title": "TensorRT Loader"
    }
  }
}"""


def generate_video_with_comfyui_trt(directory, shot_id):
    """
    This function generates an image using a prebuilt dynamic TensorRT engine

    directory -> the directory where images are stored
    positive_prompt -> the prompt to use that has been determined to describe a shot of a main character
    shot_id -> the number of the shot (00xx) that is being generated
    """

    # ComfyUI URL image upload path
    url = f"http://{server_address}/upload/image"


    # upload image
    image_path = f"output/{directory}/images/{shot_id}.png"

    data = {
      'overwrite': 'true',  # or 'false'
      'type': 'input',
      # 'subfolder': 'your_subfolder'  # Optional
    }

    # Open the image file in binary mode
    with open(image_path, 'rb') as image_file:
        files = {'image': image_file}

        # Send the POST request
        response = requests.post(url, data=data, files=files)

    # load the JSON representation of the ComfyUI workflow shown above
    prompt = json.loads(PROMPT_TEXT)

    #set the seed for our KSampler node
    prompt["4"]["inputs"]["seed"] = random.randint(0, 2**32)

    # replace image file
    prompt["7"]["inputs"]["image"] = f"{shot_id}.png"

    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
    images = get_images(ws, prompt, client_id)

    for node_id in images:
        frames = []
        for image_data in images[node_id]:
            image = Image.open(io.BytesIO(image_data))
            frames.append(image)

        video_path = f"output/{directory}/videos/{shot_id}.mp4"
        # from the diffusers library, requires opencv-python
        export_to_video(frames, video_path, fps=7)
