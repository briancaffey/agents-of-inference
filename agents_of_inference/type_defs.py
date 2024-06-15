"""
This file defines all types for structured output
"""
from typing import Annotated, List, TypedDict
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.graph.message import add_messages


class Character(BaseModel):
    """
    The type for characters that the casting agents casts for the movie
    """
    full_name: str = Field(description="The character's name")
    short_name: str = Field(description="The character's short name")
    background: str = Field(description="The character's background")
    physical_traits: str = Field(description="The physical traits of the character")
    ethnicity: str = Field(description="The character's ethnicity")
    gender: str = Field(description="The character's gender, either male of female")
    nationality: str = Field(description="The character's nationality")
    main_character: bool = Field(description="If the character is or is not the main character")

class Characters(BaseModel):
    characters: List[Character]

class Location(BaseModel):
    """
    Defines major locations that will be used in the movie
    """
    name: str = Field(description="The name of the place")
    environment: str = Field(description="A detailed description of the location's environment")
    country: str = Field(description="The country where the location is located, can possibly be unknown.")

class Locations(BaseModel):
    locations: List[Location]

class SynopsisResponse(BaseModel):
    synopsis: str = Field(description="The full synopsis of the movie")

class SynopsisFeedbackResponse(BaseModel):
    feedback: str = Field(description="The suggested feedback")

class Scene(BaseModel):
    title: str = Field(description="The title for the scene")
    content: str = Field(description="A detailed description of what happens in the scene")
    location: str = Field(description="A detailed description of where the scene takes place")

class Scenes(BaseModel):
    scenes: List[Scene]

class Shot(BaseModel):
    title: str = Field(description="Descriptive title describing the shot")
    description: str = Field(description="The densely worded description of the shot")

class Shots(BaseModel):
    shots: List[Shot]

class CharacterFilePath(BaseModel):
    filepath: str = Field(description="A filepath for a character's photo")

class CharacterFilePaths(BaseModel):
    filepaths: List[CharacterFilePath]


class AgentState(TypedDict):
    # directory under `output` for all related files
    directory: str = None
    cast: Characters = []
    locations: Locations = []

    # SYNOPSIS
    # the main synopsis
    synopsis: Annotated[list[str], add_messages]
    # feedback for each synopsis
    synopsis_feedback: Annotated[list[str], add_messages]
    final_synopsis: str = None


    # SCENES
    scenes: Scenes = []

    # SHOTS
    shots: Shots = []
