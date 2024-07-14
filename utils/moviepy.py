from io import BytesIO
import logging
import os
import warnings
import base64

import requests
from PIL import Image
from moviepy.editor import VideoClip, TextClip, CompositeVideoClip, ColorClip, VideoFileClip, concatenate_videoclips
import yaml

from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips, concatenate


def generate_documentary(state: dict):
    """
    Use moviepy to combine the mp4 files into a movie
    """
    # Suppress specific warnings
    warnings.filterwarnings("ignore", category=SyntaxWarning, module="moviepy")

    # music_files = []
    image_clips = []
    for topic in state["topics"]:
        if "shots" in topic and topic["shots"] is not None:
            for shot in topic["shots"]:
                print("processing shot")
                audio_file = shot["narration"]
                image_file = shot["image"]
                subtitle_text = shot["spoken_words"]

                narration_clip = AudioFileClip(audio_file)
                narration_duration = narration_clip.duration
                image_clip = ImageClip(image_file)
                image_clip.set_duration(narration_duration)
                # Create a text clip
                text = TextClip(subtitle_text, fontsize=70, color='white', size=(1024, 576), method="caption")

                # Set the duration of the text clip to match the video
                text = text.set_duration(image_clip.duration)

                # Set the position of the text (e.g., center)
                text = text.set_pos("center")

                # Overlay the text on the video
                clip = CompositeVideoClip([image_clip, text], use_bgclip=True)
                clip = clip.set_duration(narration_duration)
                clip = clip.set_audio(narration_clip)
                image_clips.append(clip)
    print("Concatenating image clips...")
    print(len(image_clips))
    final_video = concatenate_videoclips(image_clips)
    video_file_path = f"output/{state["directory"]}/final.mp4"
    final_video.write_videofile(video_file_path, fps=24, codec="libx264")
    # just do voice and images first
    # clips = []
    # for topic in state["topics"]:
    #     if "shots" in topic and topic["shots"] is not None:
    #         for shot in topic["shots"]:
    #             audio_clip = AudioFileClip(shot["narration"])

    # Step 2: Load the audio file and get its duration
    # audio = AudioFileClip("path/to/your/audiofile.mp3")
    # duration = audio.duration

    # # Step 3 & 4: Create a VideoClip with the image and set its duration
    # image_path = "path/to/your/image.jpg"
    # video_clip = ImageClip(image_path).set_duration(duration)

    # # Step 5: Concatenate the audio and video clips
    # final_video = concatenate_videoclips([video_clip.set_audio(audio)])

    # # Write the final video to a file
    # final_video.write_videofile("output_video.mp4", fps=24)

    # Overview of moviepy process
    # Loop over topics
    # Title page?
    # Loop over shots
    # For each shot,

    # List of video file paths
    # _id = state["directory"]
    # video_files = [f"output/{_id}/videos/00{i}.mp4" for i in range(len(os.listdir(f"output/{_id}/videos")))]

    # Load the video files
    # video_clips = [VideoFileClip(video) for video in video_files]
    # print("trying to make text clips...")
    # Create text overlays in moviepy


    # width, height = 1024, 576
    # duration = 10
    # fontsize = 30

    # # Create a black background clip
    # background_clip = ColorClip(size=(width, height), color=(0, 0, 0), duration=duration)

    # # Create text clips
    # text_clips = []
    # shots = state.get("shots")
    # for i in range(len(os.listdir(f"output/{_id}/videos"))):
    #     text = shots[i]["description"]
    #     text_clip = TextClip(text, fontsize=fontsize, color="white", method='caption', size=(800, 400), align='center')
    #     text_clip = text_clip.set_position('center').set_duration(duration)

    #     # Combine the background clip and the text clip
    #     final_clip = CompositeVideoClip([background_clip, text_clip])
    #     text_clips.append(final_clip)

    # combined = [val for pair in zip(text_clips, video_clips) for val in pair]

    # # Concatenate the video clips
    # final_clip_captioned = concatenate_videoclips(combined)
    # final_clip = concatenate_videoclips(video_clips)

    # # Save the final combined videos with and without text
    # final_clip.write_videofile(f"output/{_id}/final.mp4", codec='libx264')
    # final_clip_captioned.write_videofile(f"output/{_id}/final_captioned.mp4", codec='libx264')
    return