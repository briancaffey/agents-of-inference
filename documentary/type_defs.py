"""
This file defines all types for structured output
"""
from typing import Annotated, List, TypedDict
from langchain_core.pydantic_v1 import BaseModel, Field

class Topic(BaseModel):
    """
    Topic for documentary
    """
    name: str = Field(description="The name of the topic")
    description: str = Field(description="A description of the topic")

class Topics(BaseModel):
    topics: List[Topic] = []


class Shot(BaseModel):
    title: str = None
    visual_description: str = None
    spoken_words: str = None


class Shots(BaseModel):
    shots: List[Shot] = []


class DocumentaryState(TypedDict):
    directory: str = None
    topics: List[Topic] = []
