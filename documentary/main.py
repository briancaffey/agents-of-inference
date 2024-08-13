"""
Documentary

This file is the main entrypoint for running the Documentary program.
It generates a simple documentary to showcase how to combine generation with
text, images, video, music and voice
"""

import json
import os
import time
import argparse

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from agents_of_inference.utils import (
    save_dict_to_yaml
)
from agents_of_inference.comfyui.sd_trt import (
    generate_img_with_comfyui_trt
)
from utils.main import generate_voice, generate_music
from utils.moviepy import generate_documentary
from langchain_core.runnables.graph import MermaidDrawMethod
from langchain.output_parsers import PydanticOutputParser
from type_defs import Topics, Shots, DocumentaryState
import yaml


# env vars from .env
load_dotenv()

# Arguments
parser = argparse.ArgumentParser(description='CLI Program')
parser.add_argument('--id', type=str, help='Optional ID', default=None)
args = parser.parse_args()

# All prompts are stored centrally
with open('documentary/prompts.yml', 'r') as file:
    prompts = yaml.safe_load(file)


# Use NVIDIA API
if os.environ.get("NVIDIA_API_KEY"):
    print("== ☁️ Using NVIDIA API ☁️ ==")
    # the ChatNVIDIA class was having issues parsing output, so switching to OpenAI class
    model = ChatOpenAI(
        model="meta/llama3-70b-instruct",
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.environ.get("NVIDIA_API_KEY")
    )
else:
    # default to using local LLM
    print("## 📀 Using local models 📀 ##")
    os.environ["OPENAI_API_KEY"] = "None"
    host = "192.168.5.144" # os.environ.get("LLM_SERVICE_HOST", "192.168.1.123")
    port = "8001" # os.environ.get("LLM_SERVICE_PORT", "8000")
    # model = os.environ.get("LLM_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")
    model = "01-ai/Yi-1.5-9B-Chat"
    print(host, port, model)
    base_url = f"http://{host}:{port}/v1"
    api_key = os.environ.get("OPENAI_API_KEY", "None")
    model = ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=api_key
    )

# define state
graph = StateGraph(DocumentaryState)


#########
# NODES #
#########
def initialization_agent(state):
    """
    This agent sets up a new directory for file storage if it does not exist
    It also loads state that was previously generated if --id is passed
    This helps cache responses during development and prompt engineering
    """
    if args.id:
        # loading a cached state file
        with open(f"output/{args.id}/state.yml", 'r') as file:
            existing_state = yaml.safe_load(file)
            state = existing_state
            save_dict_to_yaml(state)
    else:
        directory = str(int(time.time()))
        state["directory"] = directory
        save_dict_to_yaml(state)
    return state

def topics_agent(state):
    """
    This agent comes up with different topics
    """

    if not state.get("topics"):
        print("## 💬 Generating topics 💬 ##")

        QUERY = """写一个故事，这个故事会被拍成一部短片，它包含5个章节。这些章节应该包括吸引人的视觉概念、风景和地点。
The response should ONLY include properly formatted JSON like this:
[
    {
      "name": "标题内容",
      "description": "描述内容"
    },
    {
      "name": "标题内容",
      "description": "描述内容"
    }
]
"""
        response = model.invoke(QUERY)

        print("== Topics response ==")
        print(response)
        print()

        # saves a list of characters to the cast key
        # I don't like this, but doing this finally got LangnChain working with TensorRT-LLM Meta-Llama-8B-Instruct
        print("======")
        print(response.content)
        print("======")
        state["topics"] = json.loads(response.content)
        save_dict_to_yaml(state)
    else:
        print("== 💬 Using cached topics 💬 ==")
    return state

def shots_agent(state):
    print("Shots Agent.....")
    for topic in state["topics"]:
        if "shots" not in topic:
            QUERY = """用中文文字回答下面的提示：
For the following story chapter, write storyboard with 5 different "shots".
Each shot must inculde a "title", "spoken_words" and "visual_description" which should be a detailed description of images to be used in the story.
Be sure to respond in Chinese. The response should only include JSON with the following format:
[
    {
      "title": "<title of the shot>",
      "spoken_words": "<spoken words to include in the shot>",
      "visual_description": "<visual description to use with stable diffusion>"
    }
]
""" + f"""
Topic: {topic["name"]}: {topic["description"]}
"""

            print(QUERY)
            response = model.invoke(QUERY)

            print("response complete")
            print("shots...")
            shots = response.content
            print(shots)
            if shots == None:
                print("⚠️ LLM Result is None! ⚠️")
                print(response)

            # fix common issues with structured output
            shots = shots.replace("\"，", "\",")
            shots = shots.replace("<|im_end|>", "")
            topic["shots"] = json.loads(shots)
        else:
            print("Using cached shots...")

    save_dict_to_yaml(state)

    return state


def translation_agent(state):

    print("Translation agent....")
    for topic in state["topics"]:
        print("Title", topic["name"])
        if "shots" in topic and topic["shots"] is not None:
            for shot in topic["shots"]:
                if "sd_prompt" not in shot:
                    translated_text = model.invoke(f"Translate the following from Chinese to English:\n\n{shot["visual_description"]}")
                    shot["sd_prompt"] = translated_text.content
                else:
                    print("using cached translation")

    save_dict_to_yaml(state)

    return state

def narration_agent(state):
    """
    Generate voice using TTS
    """
    # import sys
    # sys.exit(1)
    i = 1
    # loop over topics and shots
    print("## 💬 Narration agent 💬 ##")
    for topic in state["topics"]:
        print("Title", topic["name"])
        if "shots" in topic and topic["shots"] is not None:
            for shot in topic["shots"]:
                if "narration" not in shot:
                    print("Generating voice...")
                    generate_voice(shot["spoken_words"], int(state["directory"]), state["directory"], i)
                    shot["narration"] = f"output/{state['directory']}/narration/{i}.mp3"
                else:
                    print("== 💬 using cached narration 💬 ==")
                i += 1

    save_dict_to_yaml(state)

    return state


def music_agent(state):
    # generate a prompt for the given topic for music
    for count, topic in enumerate(state["topics"]):
        if "music" not in topic and topic["shots"] is not None:
            print("## 🎶 Generating Music 🎶 ##")
            content = " ".join([x["sd_prompt"] for x in topic["shots"]])

            # generate a prompt for music generation
            music_prompt = model.invoke(f"{prompts["music"]}:\n\n{content}")
            music_file = generate_music(music_prompt.content, state["directory"], count)
            topic["music"] = music_file
    save_dict_to_yaml(state)
    return state

def image_agent(state):
    """
    Generates an image or images for each shot in each topic
    """
    print("## 📸 Generating Images 📸 ##")
    i = 1
    for t, topic in enumerate(state["topics"]):
        if "shots" in topic and topic["shots"] is not None:
            for s, shot in enumerate(topic["shots"]):
                if "image" not in shot:
                    if "sd_prompt" in shot and shot["sd_prompt"] is not None:
                        # generate images
                        print(f"Generating image:\n\n{shot["sd_prompt"]}")
                        generate_img_with_comfyui_trt(state.get("directory"), shot["sd_prompt"], i)
                        shot["image"] = f"output/{state.get("directory")}/images/{i}.png"
                        i += 1
    save_dict_to_yaml(state)

# TODO: add SVD generation
def moviepy_agent(state):
    generate_documentary(state)
    return state


# LangGraph
graph.add_node("initialization_agent", initialization_agent)
graph.add_node("topics_agent", topics_agent)
graph.add_node("shots_agent", shots_agent)
graph.add_node("translation_agent", translation_agent)
graph.add_node("narration_agent", narration_agent)
graph.add_node("music_agent", music_agent)
graph.add_node("image_agent", image_agent)
graph.add_node("moviepy_agent", moviepy_agent)

# edges
graph.add_edge("initialization_agent", "topics_agent")
graph.add_edge("topics_agent", "shots_agent")
graph.add_edge("shots_agent", "translation_agent")
graph.add_edge("translation_agent", "narration_agent")
graph.add_edge("narration_agent", "music_agent")
graph.add_edge("music_agent", "image_agent")
graph.add_edge("image_agent", "moviepy_agent")

graph.set_entry_point("initialization_agent")
graph.set_finish_point("moviepy_agent")

runnable = graph.compile()

# draw graph
image_data = runnable.get_graph().draw_mermaid_png(
    draw_method=MermaidDrawMethod.API,
)

# Define the file path where you want to save the image
file_path = "graph.png"

# Open the file in binary write mode and write the image data
with open(file_path, "wb") as file:
    file.write(image_data)


response = runnable.invoke({
    "directory": "",
    "topics": []
})
