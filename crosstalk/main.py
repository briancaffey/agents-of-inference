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
from utils.moviepy import generate_crosstalk
from langchain_core.runnables.graph import MermaidDrawMethod
from langchain.output_parsers import PydanticOutputParser
from type_defs import Line, Lines, CrosstalkState
import yaml


# env vars from .env
load_dotenv()

# Arguments
parser = argparse.ArgumentParser(description='CLI Program')
parser.add_argument('--id', type=str, help='Optional ID', default=None)
args = parser.parse_args()

# All prompts are stored centrally
with open('crosstalk/prompts.yml', 'r') as file:
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
graph = StateGraph(CrosstalkState)


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

def lines_agent(state):
    """
    This agent comes up with the lines
    """

    if not state.get("lines"):
        print("## 💬 Generating lines 💬 ##")

        QUERY = """Write a Chinese 'crosstalk' comedy program between two people.
The topic of conversation is the US Presidential race between Donald Trump and Joe Biden and which candidate is better for China.
It should be written in Mandarin Chinese. The content for each line should be about two sentences long.
There should be about 20 lines in total.
The response should ONLY include properly formatted JSON like this:
[
    {
      "content": "说话人讲的内容",
      "speaker": "说话人的名字",
      "context": "关于所说内容的注释",
      "visual": "说话人讲的视觉描述"
    },
    {
      "content": "说话人讲的内容",
      "speaker": "说话人的名字",
      "context": "关于所说内容的注释",
      "visual": "说话人讲的视觉描述"
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
        state["lines"] = json.loads(response.content)
        save_dict_to_yaml(state)
    else:
        print("== 💬 Using cached topics 💬 ==")
    return state

def translation_agent(state):
    """
    Translates the visual descriptions to english for SD
    """

    print("Translation agent....")
    for line in state["lines"]:
        print("Title", line["content"])
        if "visual" in line and line["visual"] is not None:

            if "sd_prompt" not in line:
                translated_text = model.invoke(f"Translate the following from Chinese to English:\n\n{line["content"]}")
                line["sd_prompt"] = translated_text.content
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
    for line in state["lines"]:
        print("Content", line["content"])
        if "content" in line and line["content"] is not None:

            if "narration" not in line:
                print("Generating voice...")
                if i % 2 == 0:
                    seed = int(state["directory"])
                else:
                    seed = int(state["directory"])+1

                generate_voice(line["sd_prompt"], seed, state["directory"], i)
                line["seed"] = seed
                line["narration"] = f"output/{state['directory']}/narration/{i}.mp3"
            else:
                print("== 💬 using cached narration 💬 ==")
            i += 1

    save_dict_to_yaml(state)

    return state

def music_agent(state):
    # generate a prompt for the given topic for music
    if "music" not in state and state["music"] is not None:
        print("## 🎶 Generating Music 🎶 ##")
        MUSIC_QUERY = """
Background music for a Chinese comedy show
"""
        music_prompt = model.invoke(f"{prompts["music"]}:\n\n{MUSIC_QUERY}")
        music_file = generate_music(music_prompt.content, state["directory"], 1)
        state["music"] = music_file
    save_dict_to_yaml(state)
    return state

def image_agent(state):
    """
    Generates an image or images for each shot in each topic
    """
    print("## 📸 Generating Images 📸 ##")
    i = 1
    for l, line in enumerate(state["lines"]):
        if "visual" in line and line["visual"] is not None:

            if "image" not in line:
                # generate images
                print(f"Generating image:\n\n{line["sd_prompt"]}")
                generate_img_with_comfyui_trt(state.get("directory"), line["sd_prompt"], i)
                line["image"] = f"output/{state.get("directory")}/images/{i}.png"
                i += 1
    save_dict_to_yaml(state)

# TODO: add SVD generation
def moviepy_agent(state):
    generate_crosstalk(state)
    return state


# LangGraph
graph.add_node("initialization_agent", initialization_agent)
graph.add_node("lines_agent", lines_agent)
graph.add_node("translation_agent", translation_agent)
graph.add_node("narration_agent", narration_agent)
graph.add_node("music_agent", music_agent)
graph.add_node("image_agent", image_agent)
graph.add_node("moviepy_agent", moviepy_agent)

# edges
graph.add_edge("initialization_agent", "lines_agent")
graph.add_edge("lines_agent", "translation_agent")
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
file_path = "crosstalk_graph.png"

# Open the file in binary write mode and write the image data
with open(file_path, "wb") as file:
    file.write(image_data)


response = runnable.invoke({
    "directory": "",
    "music": "",
    "lines": []
})
