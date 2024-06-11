from io import BytesIO
import os
import warnings
import base64

import requests
from PIL import Image
from moviepy.editor import VideoClip, TextClip, CompositeVideoClip, ColorClip, VideoFileClip, concatenate_videoclips
import yaml


# TODO: move to dotenv
SD_API_URL = "http://192.168.5.96:7860"

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

def generate_headshots_for_character(file_directory, character, _id):
    """
    This function takes the character information and
    """
    directory = os.path.join('output', str(file_directory), 'images', 'characters')
    if not os.path.exists(directory):
        os.makedirs(directory)

    c = character
    prompt = f"Headshot photo of a {c.get('ethnicity')} {c.get('gender')} with {c.get('physical_traits')} simple white background"

    payload = {
        "prompt": prompt.replace("\n", "  "),
        "steps": 50,
        "width": 1024,
        "height": 1024,
    }

    # Send said payload to said URL through the API.
    response = requests.post(url=f'{SD_API_URL}/sdapi/v1/txt2img', json=payload)
    r = response.json()

    # Decode and save the image.
    with open(f"{directory}/{_id}.png", 'wb') as f:
        f.write(base64.b64decode(r['images'][0]))
    character["photos"] = [f"{_id}.png"]
    return

def generate_and_save_image(directory: str, prompt: str, id: str):
    """
    This function takes a prompt, a directory key and an id
    It generates an images using the Stable Diffusion WebUI API
    The image is saved to the corresponding location
    """
    directory = os.path.join('output', str(directory), 'images')
    if not os.path.exists(directory):
        os.makedirs(directory)

    payload = {
        "prompt": prompt.replace("\n", "  "),
        "steps": 50,
        "width": 1024,
        "height": 576,
    }

    # Send said payload to said URL through the API.
    response = requests.post(url=f'{SD_API_URL}/sdapi/v1/txt2img', json=payload)
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

def create_movie(state: dict):
    """
    Use moviepy to combine the mp4 files into a movie
    """
    # Suppress specific warnings
    warnings.filterwarnings("ignore", category=SyntaxWarning, module="moviepy")

    # List of video file paths
    _id = state["directory"]
    video_files = [f"output/{_id}/videos/00{i}.mp4" for i in range(len(os.listdir(f"output/{_id}/videos")))]

    # Load the video files
    video_clips = [VideoFileClip(video) for video in video_files]
    print("trying to make text clips...")
    # Create text overlays in moviepy


    width, height = 1024, 576
    duration = 10  # in seconds
    fontsize = 30

    # Create a black background clip
    background_clip = ColorClip(size=(width, height), color=(0, 0, 0), duration=duration)

    # Create text clips
    text_clips = []
    shots = state.get("shots")
    for i in range(len(os.listdir(f"output/{_id}/videos"))):
        text = shots[i]["description"]
        text_clip = TextClip(text, fontsize=fontsize, color="white", method='caption', size=(800, 400), align='center')
        text_clip = text_clip.set_position('center').set_duration(duration)

        # Combine the background clip and the text clip
        final_clip = CompositeVideoClip([background_clip, text_clip])
        text_clips.append(final_clip)

    combined = [val for pair in zip(text_clips, video_clips) for val in pair]

    # Concatenate the video clips
    final_clip_captioned = concatenate_videoclips(combined)
    final_clip = concatenate_videoclips(video_clips)

    # Save the final combined videos with and without text
    final_clip.write_videofile(f"output/{_id}/final.mp4", codec='libx264')
    final_clip_captioned.write_videofile(f"output/{_id}/final_captioned.mp4", codec='libx264')