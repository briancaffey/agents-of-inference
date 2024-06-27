import os
import shutil
from gradio_client import Client

client = Client("http://localhost:8080/")
result = client.predict(
		text="四川美食确实以辣闻名，但也有不辣的选择。比如甜水面、赖汤圆、蛋烘糕、叶儿粑等，这些小吃口味温和，甜而不腻，也很受欢迎。",
		temperature=0.3,
		top_P=0.7,
		top_K=20,
		audio_seed_input=2,
		text_seed_input=42,
		refine_text_flag=True,
		api_name="/generate_audio"
)


print("result:")
print(result)


# Extracting the audio file path from the result
audio_file_info = result[0]
audio_file_path = audio_file_info.split('=')[1].strip()

# Downloading the audio file
temp_dir = "\\".join(audio_file_path.split("\\")[:-1])
audio_filename = audio_file_path.split("\\")[-1]

# Create a destination folder if not exists
destination_folder = "./downloads"
os.makedirs(destination_folder, exist_ok=True)

# Move the downloaded audio file to the downloads folder
shutil.move(os.path.join(temp_dir, audio_filename), os.path.join(destination_folder, audio_filename))

# Print confirmation message
print(f"Audio has been downloaded and moved to {destination_folder}/{audio_filename}")

# Optionally, you can now rename the file or perform other operations