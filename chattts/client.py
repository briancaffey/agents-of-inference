import os
import requests

chattts_server_url = os.environ.get("CHATTTS_SERVER_URL", "192.168.5.96")
chattts_port = 8009

url = f"http://{chattts_server_url}:{chattts_port}/generate_audio"
text_data = {
    "text": "四川美食确实以辣闻名，但也有不辣的选择。比如甜水面、赖汤圆、蛋烘糕、叶儿粑等，这些小吃口味温和，甜而不腻，也很受欢迎。"
}

try:
    response = requests.post(url, json=text_data)
    response.raise_for_status()  # Raise an error for bad status codes

    audio_filename = response.headers.get('content-disposition').split('filename=')[1].strip('"')
    with open(audio_filename, 'wb') as f:
        f.write(response.content)
    print(f"Audio file has been saved as: {audio_filename}")

except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
