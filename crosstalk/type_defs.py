"""
This file defines all types for structured output
"""
from typing import List, TypedDict
from langchain_core.pydantic_v1 import BaseModel, Field

class Line(BaseModel):
    """
    Topic for documentary
    """
    content: str = Field(description="The spoken content")
    speaker: str = Field(description="The name of the speaker")
    context: str = Field(description="Contextual notes about what was spoken")
    visual: str = Field(description="Image prompt for the given line")

class Lines(BaseModel):
    topics: List[Line] = []

class CrosstalkState(TypedDict):
    directory: str = None
    music: str = None
    lines: List[Line] = []
