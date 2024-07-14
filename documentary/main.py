"""
Documentary

This file is the main entrypoint for running the Documentary program.
It generates a simple documentary to showcase how to combine generation with
text, images, video, music and voice
"""

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

        parser = JsonOutputParser(pydantic_object=Topics)

        prompt = PromptTemplate(
            template="用中文回答下写的提示：\n{format_instructions}\n{topics_query}\n",
            input_variables=["topics_query"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        chain = prompt | model | parser
        response = chain.invoke({"topics_query": prompts["topics_cn"]})

        print("== Topics response ==")
        print(response)
        print()

        # saves a list of characters to the cast key
        # I don't like this, but doing this finally got LangnChain working with TensorRT-LLM Meta-Llama-8B-Instruct

        state["topics"] = response.get("topics")
        save_dict_to_yaml(state)
    else:
        print("== 💬 Using cached topics 💬 ==")
    return state

def shots_agent(state):
    print("Shots Agent.....")
    for topic in state["topics"]:
        if "shots" not in topic:

            TEMPLATE = """Format the following response into a JSON format like this:
{"shots": [{"title": "城市晨曦", "spoken_words": "这里是公园角落的景象，宁静而温馨。", "visual_description": "一个老人在公园的角落里静静地坐在长椅上，手中拿着一卷书，旁边是一杯热气腾腾的茶。"}]}
"""
            # create shots for the given topic
            print("## 💡 Generating shots 💡 ##")
            parser = JsonOutputParser(pydantic_object=Shots)
            prompt = PromptTemplate(
                template="用中文回答下写的提示：\n{format_instructions}\n{shots_query}\n",
                input_variables=["shots_query"],
                partial_variables={"format_instructions": TEMPLATE},
            )

            chain = prompt | model | parser

            response = chain.invoke({"shots_query": prompts["shots"]})

            print("response complete")
            print("shots...")
            shots = response.get("shots")
            if shots == None:
                print("⚠️ LLM Result is None! ⚠️")
                print(response)
            topic["shots"] = shots
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


# def location_agent(state):
#     """
#     Comes up with specific important locations that will be used in the movie
#     """
#     if not state.get("locations"):
#         print("## 🗺️ Generating Locations 🗺️ ##")

#         parser = JsonOutputParser(pydantic_object=Locations)

#         prompt = PromptTemplate(
#             template="Answer the user query.\n{format_instructions}\n{locations_query}\n",
#             input_variables=["locations_query"],
#             partial_variables={"format_instructions": parser.get_format_instructions()},
#         )

#         chain = prompt | model | parser

#         response = chain.invoke({"locations_query": prompts["locations"]})
#         state["locations"] = response if type(response) == list else response.get("locations")
#         save_dict_to_yaml(state)
#     else:
#         print("== 🗺️ Using cached locations 🗺️ ==")
#     return state

# def synopsis_agent(state):
#     """
#     Provides a synopsis of the movie based on the characters and the locations.
#     """
#     if len(state.get("synopsis_feedback_history")) < 2:
#         print("## ✍️ Generating Synopsis ✍️ ##")
#         parser = PydanticOutputParser(pydantic_object=SynopsisResponse)

#         prompt = PromptTemplate(
#             template="Don't include ANYTHING except for valid JSON in your response. Answer the user query.\n{format_instructions}\n{synopsis_query}\n",
#             input_variables=["synopsis_query"],
#             partial_variables={"format_instructions": parser.get_format_instructions()},
#         )

#         chain = prompt | model | parser

#         if len(state.get("synopsis_feedback")) == 0:
#             synopsis_query = prompts.get("synopsis")
#         else:
#             synopsis_query = f"Please rewrite the synopsis based on the feedback.\nFeedback:\n{state['synopsis_feedback'][-1]}\nSynopsis:\n{state['synopsis_history'][-1]}"
#         response = chain.invoke({"synopsis_query": synopsis_query})
#         synopsis = response.synopsis

#         # TODO: clean this up
#         # 🩹 I had issues serializing the Annotated type so I store the synopsis history as a simple list of strings as well
#         state["synopsis_history"].append(synopsis)
#         state["synopsis"] = state["synopsis"] + [synopsis]
#         state["final_synopsis"] = synopsis
#     else:
#         print("== ✍️ Using Cached Synopsis ✍️ ==")

#     save_dict_to_yaml(state)

#     return state

# def synopsis_review_agent(state):
#     """
#     Provides feedback for the synopsis_agent
#     """
#     print("## 📑 Reviewing Synopsis 📑 ##")

#     parser = PydanticOutputParser(pydantic_object=SynopsisFeedbackResponse)

#     prompt = PromptTemplate(
#         template="Don't include ANYTHING except for valid JSON in your response. Answer the user query in JSON only.\n{format_instructions}\n{synopsis_feedback_query}\n",
#         input_variables=["synopsis_feedback_query"],
#         partial_variables={"format_instructions": parser.get_format_instructions()},
#     )

#     chain = prompt | model | parser

#     synopsis_feedback_query = f"Please provide specific feedback for how the following synopsis can be improved:\n\nSynopsis:\n{state["synopsis_history"][-1]}"
#     response = chain.invoke({"synopsis_feedback_query": synopsis_feedback_query})
#     synopsis_feedback = str(response.feedback)
#     state["synopsis_feedback_history"].append(synopsis_feedback)
#     state["synopsis_feedback"] = state["synopsis_feedback"] + [synopsis_feedback]
#     save_dict_to_yaml(state)
#     return state

# def scene_agent(state):
#     """
#     Generates a series of scenes based on the synopsis
#     """
#     if not state.get("scenes"):
#         print("## 📒 Generating Scenes 📒 ##")
#         parser = JsonOutputParser(pydantic_object=Scenes)

#         prompt = PromptTemplate(
#             template="ONLY include valid JSON in your response. Answer the user query.\n{format_instructions}\n{scene_query}\n",
#             input_variables=["scene_query"],
#             partial_variables={"format_instructions": parser.get_format_instructions()},
#         )

#         chain = prompt | model | parser

#         scene_query_base = prompts.get("scenes")

#         # cast/characters
#         formatted_characters = yaml.dump(state.get("cast"), default_flow_style=False)
#         characters = f"Characters:\n{formatted_characters}"

#         # locations
#         formatted_locations = yaml.dump(state.get("locations"), default_flow_style=False)
#         locations = f"Characters:\n{formatted_locations}"

#         # synopsis
#         formatted_synopsis = state.get("final_synopsis")
#         synopsis = f"Synopsis:\n{formatted_synopsis}"

#         # ask for a synopsis based on the characters and locations
#         scene_query = f"{scene_query_base}\n\n{synopsis}\n\n{characters}\n\n{locations}"

#         response = chain.invoke({"scene_query": scene_query})
#         scenes = response if type(response) == list else response.get("scenes")
#         state["scenes"] = scenes
#         save_dict_to_yaml(state)

#     else:
#         print("== 📒 Using cached scenes 📒 ==")
#     return state

# def shot_agent(state):
#     """
#     This agent goes through each scene and creates several shots.
#     Each shot has a title and content
#     The content of the shot is used later as the prompt for stable diffusion
#     """
#     if not state.get("shots"):
#         print("## 🎬 Generating Shots 🎬 ##")

#         parser = JsonOutputParser(pydantic_object=Shots)

#         prompt = PromptTemplate(
#             template="Don't include ANYTHING except for valid JSON in your response. Answer the user query.\n{format_instructions}\n{shot_query}\n",
#             input_variables=["shot_query"],
#             partial_variables={"format_instructions": parser.get_format_instructions()},
#         )

#         chain = prompt | model | parser

#         shot_query_base = prompts.get("shot")
#         shots = []
#         scene_count = len(state.get("scenes"))
#         for i, scene in enumerate(state.get("scenes")):
#             # characters
#             formatted_characters = yaml.dump(state.get("cast"), default_flow_style=False)
#             characters = f"Characters:\n{formatted_characters}"

#             # take the scene and use it to generate shots
#             scene_description = f"Scene Info:\n{scene.get('title')}\n{scene.get('content')}\n{scene.get('location')}"

#             # shot query
#             shot_query = f"{shot_query_base}\n\n{characters}\n\n{scene_description}"

#             response = chain.invoke({"shot_query": shot_query})

#             # TODO fix this
#             # 🩹 sometimes the JSON is parsed incorrectly and returns a NoneType
#             if response is None:
#                 continue


#             new_shots = response if type(response) == list else response.get("shots")

#             # TODO fix this
#             # 🩹 sometimes the JSON is parsed incorrectly
#             if len(new_shots) == 1:
#                 continue

#             print(f"## Generated {len(new_shots)} shots for scene {i+1}/{scene_count} ##")
#             shots += new_shots

#         state["shots"] = shots
#         save_dict_to_yaml(state)
#     else:
#         print("== 🎬 Using cached scenes 🎬 ==")

#     return state

# def stable_diffusion_agent(state):
#     """
#     This agent goes through each shot and generates an image based on the shot content using SD
#     """

#     print("## 📸 Generating Images 📸 ##")

#     # character_filepath_parser = JsonOutputParser(pydantic_object=CharacterFilePaths)

#     # prompt = PromptTemplate(
#     #     template="Answer the user query.\n{format_instructions}\n{character_query}\n",
#     #     input_variables=["character_query"],
#     #     partial_variables={"format_instructions": character_filepath_parser.get_format_instructions()},
#     # )

#     # chain = prompt | model | character_filepath_parser


#     # setup
#     shot_count = len(state.get("shots"))
#     # loop over all shots
#     for i, shot in enumerate(state.get("shots")):
#         description = shot.get("description")
#         if 'image' not in state["shots"][i]:
#             print()
#             print(f"00{i}/00{shot_count}")
#             print(description)
#             # TODO: add this back with character photo generation for consistent characters
#             # print("Checking for characters...")
#             # characters_photo_filepaths = chain.invoke(f"Characters: {state.get('cast')}\n Shot: {description}\n\nBase on the above information, please provide a list of the filepaths for the characters that appear in the shot description")
#             # print("Deteced the following character photo filepaths:")
#             # print(characters_photo_filepaths)

#             # generate_and_save_image(state.get("directory"), description, f"00{i}")
#             generate_and_save_image_comfyui(state.get("directory"), description, f"00{i}")
#             print(f"Generated image output/{state["directory"]}/images/00{i}.png")
#             state["shots"][i]["image"] = f"00{i}.png"
#             save_dict_to_yaml(state)

#     return state

# def stable_video_diffusion_agent(state):
#     """
#     This agent loops over the files in output/{id}/images/ and generates videos from images
#     It uses the Stable Video Diffusion FastAPI service that is defined in the `svd` directory
#     """
#     print("## 🎥 Generating Video 🎥 ##")
#     for i, shot in enumerate(state.get("shots")):
#         if 'video' not in state["shots"][i]:
#             generate_and_save_video(state["directory"], f"00{i}.png")
#             # generate_video(state["directory"], f"00{i}")
#             print(f"Generated video output/{state["directory"]}/videos/00{i}.mp4")
#             state["shots"][i]["video"] = f"00{i}.mp4"
#             save_dict_to_yaml(state)

#     return state

# def video_editing_agent(state):
#     """
#     Uses moviepy to create a video from mp4 files created by stable_video_diffusion_agent
#     """
#     print("## ✂️ Editing Video ✂️ ##")
#     create_movie(state)
#     return state


# LangGraph
graph.add_node("initialization_agent", initialization_agent)
graph.add_node("topics_agent", topics_agent)
graph.add_node("shots_agent", shots_agent)
graph.add_node("translation_agent", translation_agent)
graph.add_node("narration_agent", narration_agent)
graph.add_node("music_agent", music_agent)
graph.add_node("image_agent", image_agent)
graph.add_node("moviepy_agent", moviepy_agent)
# graph.add_node("next_agent", next_agent)


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
