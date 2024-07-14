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

# main infer params
body = {
    "text": [
        "当夜幕降临，都市展现出另一番景象。高楼的霓虹灯闪烁着耀眼的光芒，车流像河流一样在街道上流淌，夜市的小摊上飘散着诱人的食物香味。"
    ],
    "stream": False,
    "lang": None,
    "skip_refine_text": False,
    "refine_text_only": False,
    "use_decoder": True,
    "audio_seed": None,
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
    "prompt": "[speed_5]",
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
        dt = datetime.datetime.now()
        ts = int(dt.timestamp())
        tgt = f"./output/{ts}/"
        os.makedirs(tgt, 0o755)
        zip_ref.extractall(tgt)
        print("Extracted files into", tgt)

except requests.exceptions.RequestException as e:
    print(f"Request Error: {e}")
