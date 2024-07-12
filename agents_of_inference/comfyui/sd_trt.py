"""
This workflow generates a simple 1024x576 image based on a prompt
- It uses TensorRT to generate images in seconds

For reference: https://github.com/comfyanonymous/ComfyUI_TensorRT
"""


import io
import os
import json
import random
import uuid

import websocket
from PIL import Image

from .utils import get_images

comfyui_service_host = os.environ.get("COMFYUI_SERVICE_HOST", "192.168.5.96")
comfyui_service_port = os.environ.get("COMFYUI_SERVICE_PORT", "8188")

server_address = f"{comfyui_service_host}:{comfyui_service_port}"
client_id = str(uuid.uuid4())

# Similar to the example workflow show here:
# https://github.com/comfyanonymous/ComfyUI_TensorRT/tree/master?tab=readme-ov-file#common-issueslimitations
PROMPT_TEXT = """{
  "3": {
    "inputs": {
      "seed": 606808256324937,
      "steps": 50,
      "cfg": 8,
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 1,
      "model": [
        "10",
        0
      ],
      "positive": [
        "6",
        0
      ],
      "negative": [
        "7",
        0
      ],
      "latent_image": [
        "5",
        0
      ]
    },
    "class_type": "KSampler",
    "_meta": {
      "title": "KSampler"
    }
  },
  "4": {
    "inputs": {
      "ckpt_name": "sd_xl_base_1.0_0.9vae.safetensors"
    },
    "class_type": "CheckpointLoaderSimple",
    "_meta": {
      "title": "Load Checkpoint"
    }
  },
  "5": {
    "inputs": {
      "width": 1024,
      "height": 576,
      "batch_size": 1
    },
    "class_type": "EmptyLatentImage",
    "_meta": {
      "title": "Empty Latent Image"
    }
  },
  "6": {
    "inputs": {
      "text": "replace me!",
      "clip": [
        "4",
        1
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP Text Encode (Prompt)"
    }
  },
  "7": {
    "inputs": {
      "text": "cartoon, drawing, digital art, anime, manga",
      "clip": [
        "4",
        1
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP Text Encode (Prompt)"
    }
  },
  "8": {
    "inputs": {
      "samples": [
        "3",
        0
      ],
      "vae": [
        "4",
        2
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "9": {
    "inputs": {
      "filename_prefix": "aoi",
      "images": [
        "8",
        0
      ]
    },
    "class_type": "SaveImage",
    "_meta": {
      "title": "Save Image"
    }
  },
  "10": {
    "inputs": {
      "unet_name": "ComfyUI_DYN_$dyn-b-1-1-1-h-576-576-576-w-1024-1024-1024_00001_.engine",
      "model_type": "sdxl_base"
    },
    "class_type": "TensorRTLoader",
    "_meta": {
      "title": "TensorRT Loader"
    }
  }
}"""


def generate_img_with_comfyui_trt(directory, positive_prompt, shot_id):
    """
    This function generates an image using a prebuilt dynamic TensorRT engine

    directory -> the directory where images are stored
    positive_prompt -> the prompt to use that has been determined to describe a shot of a main character
    shot_id -> the number of the shot (00xx) that is being generated
    """

    # # ComfyUI URL image upload path
    # url = f"http://{server_address}/upload/image"

    # load the JSON representation of the ComfyUI workflow shown above
    prompt = json.loads(PROMPT_TEXT)
    #set the text prompt for our positive CLIPTextEncode
    prompt["6"]["inputs"]["text"] = positive_prompt

    #set the seed for our KSampler node
    prompt["3"]["inputs"]["seed"] = random.randint(0, 2**32)

    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
    images = get_images(ws, prompt, client_id)

    for node_id in images:
        for image_data in images[node_id]:
            image = Image.open(io.BytesIO(image_data))
            image.save(f"output/{directory}/images/{shot_id}.png")
