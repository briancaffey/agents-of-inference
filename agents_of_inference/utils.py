from io import BytesIO
import os
import warnings
import base64

import requests
from PIL import Image
from moviepy.editor import VideoFileClip, concatenate_videoclips
import yaml


def save_dict_to_yaml(dictionary):
    """
    This is called at the end of every agent function that produces LLM output
    The YAML file is saved and on subsequent runs the LLM responses are read from
    the YAML file and are not generated again, caching the LLM responses
    """
    if 'directory' in dictionary:
        directory = os.path.join('output', dictionary['directory'])
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(os.path.join(directory, 'state.yml'), 'w') as f:
            yaml.dump(dictionary, f)
    else:
        print("Error: 'directory' key is missing in the dictionary.")


def generate_and_save_image(directory: str, prompt: str, id: str):
    """
    This function takes a prompt, a directory key and an id
    It generates an images using the Stable Diffusion WebUI API
    The image is saved to the corresponding location
    """
    directory = os.path.join('output', str(directory), 'images')
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Define the URL and the payload to send.
    url = "http://192.168.5.96:7860"

    payload = {
        "prompt": prompt.replace("\n", "  "),
        "steps": 50,
        "width": 1024,
        "height": 576,
    }

    # Send said payload to said URL through the API.
    response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)
    r = response.json()

    # Decode and save the image.
    with open(f"{directory}/{id}.png", 'wb') as f:
        f.write(base64.b64decode(r['images'][0]))

def generate_and_save_video(id: str, image_path: str):
    """
    This function takes a path to an image and uses an external SVD service to generate video
    The SVD service is defined in the `svd` directory of this repository
    """
    directory = os.path.join('output', str(id), 'videos')
    if not os.path.exists(directory):
        os.makedirs(directory)

    url = "http://192.168.5.96:8000/api/img2vid"

    # Prepare the image to be used in the HTTP request
    img = Image.open(f"output/{id}/images/{image_path}")
    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    # Use a more readable way to prepare files for the request
    files = {"image_file": ("image.png", img_bytes, "image/png")}

    try:
        response = requests.post(url, files=files)
        response.raise_for_status()  # Raise an error for bad responses

        video_file_name = image_path.replace(".png", "")
        video_path = os.path.join(directory, f"{video_file_name}.mp4")

        # Save the received video file
        with open(video_path, "wb") as f:
            f.write(response.content)

        print("== stable video diffusion generation complete ==")
    except requests.exceptions.RequestException as e:
        print(f"HTTP request failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

def create_movie(id: str):
    """
    Use moviepy to combine the mp4 files into a movie
    """
    # Suppress specific warnings
    warnings.filterwarnings("ignore", category=SyntaxWarning, module="moviepy")

    # List of video file paths

    video_files = [f"output/{id}/videos/00{i}.mp4" for i in range(len(os.listdir(f"output/{id}/videos")))]

    # Load the video files
    video_clips = [VideoFileClip(video) for video in video_files]

    # Concatenate the video clips
    final_clip = concatenate_videoclips(video_clips)

    # Save the final combined video
    final_clip.write_videofile(f"output/{id}/final.mp4", codec='libx264')