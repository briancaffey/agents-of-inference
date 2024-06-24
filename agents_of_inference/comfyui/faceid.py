"""
This file implements a workflow that I built manually with the
ComfyUI graph system for implementing face transfer

credit: Latent Vision
"""


import io
import os
import json
import random
import uuid
import urllib.request
import urllib.parse

import websocket
from PIL import Image
import requests

from .utils import get_images

server_address = os.environ.get("COMFYUI_SERVER_ADDRESS", "192.168.5.96:8188")
client_id = str(uuid.uuid4())

# this workflow uses IPAdapter FaceID
# https://github.com/cubiq/ComfyUI_IPAdapter_plus
prompt_text = """{
  "3": {
    "inputs": {
      "seed": 332350731500952,
      "steps": 50,
      "cfg": 10.46,
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 1,
      "model": [
        "18",
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
      "ckpt_name": "albedobaseXL_v21.safetensors"
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
      "text": "replaced by script below...",
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
      "text": "",
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
      "filename_prefix": "IPAdapter",
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
  "12": {
    "inputs": {
      "image": "replaced_below.png",
      "upload": "image"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "18": {
    "inputs": {
      "weight": 1,
      "weight_faceidv2": 2,
      "weight_type": "linear",
      "combine_embeds": "concat",
      "start_at": 0,
      "end_at": 1,
      "embeds_scaling": "V only",
      "model": [
        "20",
        0
      ],
      "ipadapter": [
        "20",
        1
      ],
      "image": [
        "12",
        0
      ]
    },
    "class_type": "IPAdapterFaceID",
    "_meta": {
      "title": "IPAdapter FaceID"
    }
  },
  "20": {
    "inputs": {
      "preset": "FACEID PLUS V2",
      "lora_strength": 0.78,
      "provider": "CPU",
      "model": [
        "4",
        0
      ]
    },
    "class_type": "IPAdapterUnifiedLoaderFaceID",
    "_meta": {
      "title": "IPAdapter Unified Loader FaceID"
    }
  },
  "21": {
    "inputs": {
      "width": 1024,
      "height": 576,
      "x": 512,
      "y": 512,
      "image": [
        "12",
        0
      ]
    },
    "class_type": "ImageCrop",
    "_meta": {
      "title": "ImageCrop"
    }
  }
}
"""


def generate_img_with_face(directory, positive_prompt, face_image_filepath, shot_id):
    """
    This function generates an image using the IPAdapter FaceID workflow above

    directory -> the directory where images are stored
    positive_prompt -> the prompt to use that has been determined to describe a shot of a main character
    face_image_uuid -> the UUID of the image with the character's face
    shot_id -> the number of the shot (00xx) that is being generated
    """

    # ComfyUI URL image upload path
    url = f"http://{server_address}/upload/image"

    # upload image
    image_path = face_image_filepath

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


    # Check the response
    if response.status_code == 200:
        print('Image uploaded successfully!')
        print('Response:', response.json())
    else:
        print('Failed to upload image. Status code:', response.status_code)
        print('Response:', response.text)

    prompt = json.loads(prompt_text)
    #set the text prompt for our positive CLIPTextEncode
    prompt["6"]["inputs"]["text"] = positive_prompt

    # input image (face)
    # the filepath is the file name (and path) in the inputs directory in ComfyUI
    prompt["12"]["inputs"]["image"] = f"{shot_id}.png"

    #set the seed for our KSampler node
    prompt["3"]["inputs"]["seed"] = random.randint(0, 2**32)

    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
    images = get_images(ws, prompt, client_id)

    #Commented out code to display the output images:

    for node_id in images:
        for image_data in images[node_id]:
            image = Image.open(io.BytesIO(image_data))
            image.save(f"output/{directory}/images/{shot_id}.png")
