"""
Agents of Inference

This file is the main entrypoint for running the Agents of Inference program

The program uses large language models (LLMs) and stable diffusion (SD) and
stable video diffusion (SVD) to generate short films.
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
from utils import (
    save_dict_to_yaml,
    generate_and_save_image,
    generate_and_save_image_comfyui,
    generate_video,
    generate_and_save_video,
    # generate_headshots_for_character, # Pause temporarily
    create_movie
)
from langchain_core.runnables.graph import MermaidDrawMethod
from langchain.output_parsers import PydanticOutputParser
from type_defs import AgentState, Characters, Locations, SynopsisResponse, SynopsisFeedbackResponse, Scenes, Shots, CharacterFilePaths
import yaml


# env vars from .env
load_dotenv()

# Arguments
parser = argparse.ArgumentParser(description='CLI Program')
parser.add_argument('--id', type=str, help='Optional ID', default=None)
args = parser.parse_args()

# All prompts are stored centrally
with open('agents_of_inference/prompts.yml', 'r') as file:
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
    host = os.environ.get("HOST", "192.168.1.123")
    port = os.environ.get("PORT", "8000")
    model = ChatOpenAI(
        model="meta/llama3-8b-instruct",
        base_url=f"http://{host}:{port}/v1",
        api_key=os.environ.get("OPENAI_API_KEY")
    )

# define state
graph = StateGraph(AgentState)


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

def casting_agent(state):
    """
    This agent casts the characters that will appear in the show
    """
    if not state.get("cast"):
        print("## 🎭 Generating Cast 🎭 ##")

        parser = JsonOutputParser(pydantic_object=Characters)

        prompt = PromptTemplate(
            template="Don't include ANYTHING except for valid JSON in your response. Answer the user query in JSON only.\n{format_instructions}\n{casting_query}\n",
            input_variables=["casting_query"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        chain = prompt | model | parser

        response = chain.invoke({"casting_query": prompts["casting"]})

        # saves a list of characters to the cast key
        # I don't like this, but doing this finally got LangnChain working with TensorRT-LLM Meta-Llama-8B-Instruct
        state["cast"] = response if type(response) == list else response.get("characters")

        # TODO: add this back in
        # # generate photos of each character that can later be used for consistant characters
        # for i, character in enumerate(state["cast"]):
        #     image_id = str(uuid.uuid4())
        #     generate_headshots_for_character(state["directory"], character, image_id)
        #     save_dict_to_yaml(state)
        save_dict_to_yaml(state)
    else:
        print("== 🎭 Using cached cast 🎭 ==")
    return state

def location_agent(state):
    """
    Comes up with specific important locations that will be used in the movie
    """
    if not state.get("locations"):
        print("## 🗺️ Generating Locations 🗺️ ##")

        parser = JsonOutputParser(pydantic_object=Locations)

        prompt = PromptTemplate(
            template="Answer the user query.\n{format_instructions}\n{locations_query}\n",
            input_variables=["locations_query"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        chain = prompt | model | parser

        response = chain.invoke({"locations_query": prompts["locations"]})
        state["locations"] = response if type(response) == list else response.get("locations")
        save_dict_to_yaml(state)
    else:
        print("== 🗺️ Using cached locations 🗺️ ==")
    return state

def synopsis_agent(state):
    """
    Provides a synopsis of the movie based on the characters and the locations.
    """
    if len(state.get("synopsis_feedback_history")) < 2:
        print("## ✍️ Generating Synopsis ✍️ ##")
        parser = PydanticOutputParser(pydantic_object=SynopsisResponse)

        prompt = PromptTemplate(
            template="Don't include ANYTHING except for valid JSON in your response. Answer the user query.\n{format_instructions}\n{synopsis_query}\n",
            input_variables=["synopsis_query"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        chain = prompt | model | parser

        if len(state.get("synopsis_feedback")) == 0:
            synopsis_query = prompts.get("synopsis")
        else:
            synopsis_query = f"Please rewrite the synopsis based on the feedback.\nFeedback:\n{state['synopsis_feedback'][-1]}\nSynopsis:\n{state['synopsis_history'][-1]}"
        response = chain.invoke({"synopsis_query": synopsis_query})
        synopsis = response.synopsis

        # TODO: clean this up
        # 🩹 I had issues serializing the Annotated type so I store the synopsis history as a simple list of strings as well
        state["synopsis_history"].append(synopsis)
        state["synopsis"] = state["synopsis"] + [synopsis]
        state["final_synopsis"] = synopsis
    else:
        print("== ✍️ Using Cached Synopsis ✍️ ==")

    save_dict_to_yaml(state)

    return state

def synopsis_review_agent(state):
    """
    Provides feedback for the synopsis_agent
    """
    print("## 📑 Reviewing Synopsis 📑 ##")

    parser = PydanticOutputParser(pydantic_object=SynopsisFeedbackResponse)

    prompt = PromptTemplate(
        template="Don't include ANYTHING except for valid JSON in your response. Answer the user query in JSON only.\n{format_instructions}\n{synopsis_feedback_query}\n",
        input_variables=["synopsis_feedback_query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | model | parser

    synopsis_feedback_query = f"Please provide specific feedback for how the following synopsis can be improved:\n\nSynopsis:\n{state["synopsis_history"][-1]}"
    response = chain.invoke({"synopsis_feedback_query": synopsis_feedback_query})
    synopsis_feedback = str(response.feedback)
    state["synopsis_feedback_history"].append(synopsis_feedback)
    state["synopsis_feedback"] = state["synopsis_feedback"] + [synopsis_feedback]
    save_dict_to_yaml(state)
    return state

def scene_agent(state):
    # exit(1)
    if not state.get("scenes"):
        print("## 📒 Generating Scenes 📒 ##")
        parser = JsonOutputParser(pydantic_object=Scenes)

        prompt = PromptTemplate(
            template="ONLY include valid JSON in your response. Answer the user query.\n{format_instructions}\n{scene_query}\n",
            input_variables=["scene_query"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        chain = prompt | model | parser

        scene_query_base = prompts.get("scenes")

        # cast/characters
        formatted_characters = yaml.dump(state.get("cast"), default_flow_style=False)
        characters = f"Characters:\n{formatted_characters}"

        # locations
        formatted_locations = yaml.dump(state.get("locations"), default_flow_style=False)
        locations = f"Characters:\n{formatted_locations}"

        # synopsis
        formatted_synopsis = state.get("final_synopsis")
        synopsis = f"Synopsis:\n{formatted_synopsis}"

        # ask for a synopsis based on the characters and locations
        scene_query = f"{scene_query_base}\n\n{synopsis}"

        response = chain.invoke({"scene_query": scene_query})
        scenes = response if type(response) == list else response.get("scenes")
        state["scenes"] = scenes
        save_dict_to_yaml(state)

    else:
        print("== 📒 Using cached scenes 📒 ==")
    return state

def shot_agent(state):
    """
    This agent goes through each scene and creates several shots.
    Each shot has a title and content
    The content of the shot is used later as the prompt for stable diffusion
    """
    if not state.get("shots"):
        print("## 🎬 Generating Shots 🎬 ##")

        parser = JsonOutputParser(pydantic_object=Shots)

        prompt = PromptTemplate(
            template="Don't include ANYTHING except for valid JSON in your response. Answer the user query.\n{format_instructions}\n{shot_query}\n",
            input_variables=["shot_query"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        chain = prompt | model | parser

        shot_query_base = prompts.get("shot")
        shots = []
        scene_count = len(state.get("scenes"))
        for i, scene in enumerate(state.get("scenes")):
            # characters
            formatted_characters = yaml.dump(state.get("cast"), default_flow_style=False)
            characters = f"Characters:\n{formatted_characters}"

            # take the scene and use it to generate shots
            scene_description = f"Scene Info:\n{scene.get('title')}\n{scene.get('content')}\n{scene.get('location')}"

            # shot query
            shot_query = f"{shot_query_base}\n\n{characters}\n\n{scene_description}"

            response = chain.invoke({"shot_query": shot_query})


            new_shots = response if type(response) == list else response.get("shots")

            # TODO fix this
            # 🩹 sometimes the JSON is parsed incorrectly
            if len(new_shots) == 1:
                continue

            print(f"## Generated {len(new_shots)} shots for scene {i+1}/{scene_count} ##")
            shots += new_shots

        state["shots"] = shots
        save_dict_to_yaml(state)
    else:
        print("== 🎬 Using cached scenes 🎬 ==")

    return state

def stable_diffusion_agent(state):
    """
    This agent goes through each shot and generates an image based on the shot content using SD
    """

    character_filepath_parser = JsonOutputParser(pydantic_object=CharacterFilePaths)

    prompt = PromptTemplate(
        template="Answer the user query.\n{format_instructions}\n{character_query}\n",
        input_variables=["character_query"],
        partial_variables={"format_instructions": character_filepath_parser.get_format_instructions()},
    )

    chain = prompt | model | character_filepath_parser


    # setup
    shot_count = len(state.get("shots"))
    # loop over all shots
    for i, shot in enumerate(state.get("shots")):
        description = shot.get("description")
        if 'image' not in state["shots"][i]:
            print()
            print(f"00{i}/00{shot_count}")
            print(description)
            # TODO: add this back with character photo generation for consistent characters
            # print("Checking for characters...")
            # characters_photo_filepaths = chain.invoke(f"Characters: {state.get('cast')}\n Shot: {description}\n\nBase on the above information, please provide a list of the filepaths for the characters that appear in the shot description")
            # print("Deteced the following character photo filepaths:")
            # print(characters_photo_filepaths)

            # generate_and_save_image(state.get("directory"), description, f"00{i}")
            generate_and_save_image_comfyui(state.get("directory"), description, f"00{i}")
            print(f"Generated image output/{state["directory"]}/images/00{i}.png")
            state["shots"][i]["image"] = f"00{i}.png"
            save_dict_to_yaml(state)

    return state

def stable_video_diffusion_agent(state):
    """
    This agent loops over the files in output/{id}/images/ and generates videos from images
    It uses the Stable Video Diffusion FastAPI service that is defined in the `svd` directory
    """
    for i, shot in enumerate(state.get("shots")):
        if 'video' not in state["shots"][i]:
            # generate_and_save_video(state["directory"], f"00{i}.png")
            generate_video(state["directory"], f"00{i}")
            print(f"Generated video output/{state["directory"]}/videos/00{i}.mp4")
            state["shots"][i]["video"] = f"00{i}.mp4"
            save_dict_to_yaml(state)

    return state

def video_editing_agent(state):
    """
    Uses moviepy to create a video from mp4 files created by stable_video_diffusion_agent
    """
    create_movie(state)
    return state

##############
# CONDITIONS #
##############
# State in conditions is read only! we don't return state from these functions just the name of the next node
def synopsis_condition(state):
    # check to see how many revisions have been done
    if len(state["synopsis_feedback_history"]) < 2:
        print("## going to synopsis_review_agent ##")
        return "synopsis_review_agent"
    print("## going to scene_agent ##")
    return "scene_agent"

# define graph
graph.add_node("initialization_agent", initialization_agent)
graph.add_node("casting_agent", casting_agent)
graph.add_node("location_agent", location_agent)
graph.add_node("synopsis_agent", synopsis_agent)
graph.add_node("synopsis_review_agent", synopsis_review_agent)
graph.add_node("scene_agent", scene_agent)
graph.add_node("shot_agent", shot_agent)
graph.add_node("stable_diffusion_agent", stable_diffusion_agent)
graph.add_node("stable_video_diffusion_agent", stable_video_diffusion_agent)
graph.add_node("video_editing_agent", video_editing_agent)

graph.add_edge("initialization_agent", "casting_agent")
graph.add_edge("casting_agent", "location_agent")
graph.add_edge("location_agent", "synopsis_agent")
graph.add_conditional_edges("synopsis_agent", synopsis_condition, ["synopsis_review_agent", "scene_agent"])
graph.add_edge("synopsis_review_agent", "synopsis_agent")
graph.add_edge("scene_agent", "shot_agent")
graph.add_edge("shot_agent", "stable_diffusion_agent")
graph.add_edge("stable_diffusion_agent", "stable_video_diffusion_agent")
graph.add_edge("stable_video_diffusion_agent", "video_editing_agent")

graph.set_entry_point("initialization_agent")
graph.set_finish_point("video_editing_agent")

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
    "cast": [],
    "directory": "",
    "locations": [],
    "synopsis": [],
    "synopsis_history": [],
    "synopsis_feedback": [],
    "synopsis_feedback_history": [],
    "final_synopsis": "",
    "scenes": [],
    "shots": [],
})
