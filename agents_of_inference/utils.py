import yaml
import os
import requests
import base64

def save_dict_to_yaml(dictionary):
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
        "height": 1024,
    }

    # Send said payload to said URL through the API.
    response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)
    r = response.json()

    # Decode and save the image.
    with open(f"{directory}/{id}.png", 'wb') as f:
        f.write(base64.b64decode(r['images'][0]))
