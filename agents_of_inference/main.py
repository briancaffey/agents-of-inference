import os
import time
import argparse
import uuid

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langgraph.graph import StateGraph
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from utils import (
    save_dict_to_yaml,
    generate_and_save_image,
    generate_and_save_video,
    generate_headshots_for_character,
    create_movie
)
from langchain_core.runnables.graph import MermaidDrawMethod
from type_defs import AgentState, Characters, Locations, Synopsis, Scenes, Shots, CharacterFilePaths
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
    model = ChatNVIDIA(model="meta/llama3-70b-instruct")
else:
    # default to using local LLM
    print("## 📀 Using local models 📀 ##")
    os.environ["OPENAI_API_KEY"] = "None"
    model = ChatOpenAI(model="llama3", base_url="http://192.168.5.96:5001/v1")

# define state
graph = StateGraph(AgentState)

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
            template="Answer the user query.\n{format_instructions}\n{casting_query}\n",
            input_variables=["casting_query"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        chain = prompt | model | parser

        response = chain.invoke({"casting_query": prompts["casting"]})

        # saves a list of characters to the cast key
        state["cast"] = response.get("characters")

        # generate photos of each character that can later be used for consistant characters
        for i, character in enumerate(state["cast"]):
            image_id = str(uuid.uuid4())
            generate_headshots_for_character(state["directory"], character, image_id)
            save_dict_to_yaml(state)
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
        state["locations"] = response.get("locations")
        save_dict_to_yaml(state)
    else:
        print("== 🗺️ Using cached locations 🗺️ ==")
    return state

def synopsis_agent(state):
    """
    Provides a synopsis of the movie based on the characters and the locations.
    """
    if not state.get("synopsis"):
        print("## 📝 Generating Synopsis 📝 ##")
        parser = JsonOutputParser(pydantic_object=Synopsis)

        prompt = PromptTemplate(
            template="Answer the user query.\n{format_instructions}\n{synopsis_query}\n",
            input_variables=["synopsis_query"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        chain = prompt | model | parser

        synopsis_query_base = prompts.get("synopsis")

        # cast/characters
        formatted_characters = yaml.dump(state.get("cast"), default_flow_style=False)
        characters = f"Characters:\n{formatted_characters}"

        # locations
        formatted_locations = yaml.dump(state.get("locations"), default_flow_style=False)
        locations = f"Characters:\n{formatted_locations}"

        # ask for a synopsis based on the characters and locations
        synopsis_query = f"{synopsis_query_base}\n\n{characters}\n\n{locations}"

        response = chain.invoke({"synopsis_query": synopsis_query})
        synopsis = response.get("synopsis")
        state["synopsis"] = synopsis
        save_dict_to_yaml(state)

    else:
        print("== 📝 Using cached synopsis 📝 ==")
    return state

def scene_agent(state):
    if not state.get("scenes"):
        print("## 📒 Generating Scenes 📒 ##")
        parser = JsonOutputParser(pydantic_object=Scenes)

        prompt = PromptTemplate(
            template="Answer the user query.\n{format_instructions}\n{scene_query}\n",
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
        formatted_synopsis = yaml.dump(state.get("synopsis"), default_flow_style=False)
        synopsis = f"Synopsis:\n{formatted_synopsis}"

        # ask for a synopsis based on the characters and locations
        scene_query = f"{scene_query_base}\n\n{characters}\n\n{locations}\n\n{synopsis}"

        response = chain.invoke({"scene_query": scene_query})
        scenes = response.get("scenes")
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
            template="Answer the user query.\n{format_instructions}\n{shot_query}\n",
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
            print(f"## Generated {len(response.get('shots'))} shots for scene {i+1}/{scene_count} ##")

            shots += response.get("shots")

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
            print("Checking for characters...")
            characters_photo_filepaths = chain.invoke(f"Characters: {state.get('cast')}\n Shot: {description}\n\nBase on the above information, please provide a list of the filepaths for the characters that appear in the shot description")
            print("Deteced the following character photo filepaths:")
            print(characters_photo_filepaths)

            generate_and_save_image(state.get("directory"), description, f"00{i}")
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
            generate_and_save_video(state["directory"], f"00{i}.png")
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

# define graph
graph.add_node("initialization_agent", initialization_agent)
graph.add_node("casting_agent", casting_agent)
graph.add_node("location_agent", location_agent)
graph.add_node("synopsis_agent", synopsis_agent)
graph.add_node("scene_agent", scene_agent)
graph.add_node("shot_agent", shot_agent)
graph.add_node("stable_diffusion_agent", stable_diffusion_agent)
graph.add_node("stable_video_diffusion_agent", stable_video_diffusion_agent)
graph.add_node("video_editing_agent", video_editing_agent)

graph.add_edge("initialization_agent", "casting_agent")
graph.add_edge("casting_agent", "location_agent")
graph.add_edge("location_agent", "synopsis_agent")
graph.add_edge("synopsis_agent", "scene_agent")
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
    "synopsis": "",
    "scenes": [],
    "shots": [],
})
