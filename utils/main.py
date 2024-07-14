from io import BytesIO
import logging
import datetime
import os
import warnings
import base64

import requests


import datetime
import os
import zipfile
from io import BytesIO

from dotenv import load_dotenv
import requests

load_dotenv()

chattts_service_host = os.environ.get("CHATTTS_SERVICE_HOST", "localhost")
chattts_service_port = os.environ.get("CHATTTS_SERVICE_PORT", "8007")

chattts_service_host = "192.168.5.144"
chattts_service_port = "8007"

CHATTTS_URL = f"http://{chattts_service_host}:{chattts_service_port}/generate_voice"
print(CHATTTS_URL)

def generate_voice(text: str, audio_seed: int = None, directory: str = None, count: int = 0):
    """
    This function generates voice data for `text` using ChatTTS
    """
    # main infer params
    body = {
        "text": [text],
        "stream": False,
        "lang": None,
        "skip_refine_text": False,
        "refine_text_only": False,
        "use_decoder": True,
        "audio_seed": audio_seed,
        "text_seed": None,
        "do_text_normalization": True,
        "do_homophone_replacement": False,
    }

    # refine text params
    params_refine_text = {
        "prompt": "",
        "top_P": 0.7,
        "top_K": 20,
        "temperature": 0.7,
        "repetition_penalty": 1,
        "max_new_token": 384,
        "min_new_token": 0,
        "show_tqdm": True,
        "ensure_non_empty": True,
        "stream_batch": 24,
    }
    body["params_refine_text"] = params_refine_text

    # infer code params
    params_infer_code = {
        "prompt": "",
        "top_P": 0.1,
        "top_K": 20,
        "temperature": 0.3,
        "repetition_penalty": 1.05,
        "max_new_token": 2048,
        "min_new_token": 0,
        "show_tqdm": True,
        "ensure_non_empty": True,
        "stream_batch": True,
        "spk_emb": None,
    }
    body["params_infer_code"] = params_infer_code


    try:
        response = requests.post(CHATTTS_URL, json=body)
        response.raise_for_status()
        with zipfile.ZipFile(BytesIO(response.content), "r") as zip_ref:

            # save files for each request in a different folder
            tgt = f"./output/{directory}/narration"
            os.makedirs(tgt, 0o755, exist_ok=True)
            zip_ref.extractall(tgt)
            # rename extracted file with file counter
            os.rename(f"./output/{directory}/narration/0.mp3", f"./output/{directory}/narration/{count}.mp3")
            print("Extracted files into", tgt)

    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")


def generate_music(text: str, directory: str = None, count: int = 0) -> str:
    """
    Generates 30 second music audio based on a text prompt
    Saves file to directory
    """
    MUSICGEN_SERVICE_HOST = os.environ.get("MUSICGEN_SERVICE_HOST", "192.168.1.123")
    MUSICGEN_SERVICE_PORT = os.environ.get("MUSICGEN_SERVICE_PORT", "8011")

    MUSICGEN_SERVICE_HOST = "192.168.5.96"
    MUSICGEN_SERVICE_PORT = "8011"

    url = f"http://{MUSICGEN_SERVICE_HOST}:{MUSICGEN_SERVICE_PORT}/generate_music"
    print("URL for musicgen ", url)

    print(f"Music prompt: {text}")
    response = requests.post(url, json={"description": text, "duration": 30})
    print("Music generation complete")

    tgt = f"output/{directory}/music/"
    os.makedirs(tgt, 0o755, exist_ok=True)


    if response.status_code == 200:
        filename = f"output/{directory}/music/{count}.wav"
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"Music generated and saved to {filename}")
        return filename
    else:
        print("Failed to generate music:", response.status_code, response.text)

