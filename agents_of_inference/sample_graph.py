"""
This is a sandbox for testing out LangGraph features

Run the following:

python agents_of_inference/sample_graph.py

An image in the root directory called `sample_graph.py` will be created
"""


import os
import time
import argparse
import uuid
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages

from langchain_core.runnables.graph import MermaidDrawMethod

class SampleState(TypedDict):
    text: Annotated[list, add_messages]
    review_count: int

REVIEW_LIMIT = 5

# define state
graph = StateGraph(SampleState)

def a(state):
    print("in node A")
    return state

def b(state):
    print("in node B")
    return state

def c(state):
    print("in node C")
    return state

def d(state):
    print("in node D")
    state["review_count"] += 1
    return state

def e(state):
    print("in node E")
    return state

def f(state):
    print("in node F")
    return state


def cond(state):
    # print(state)
    print("evaluating condition")
    if state["review_count"] < REVIEW_LIMIT:
        print("going to d")
        return "d"
    else:
        return "e"

def fcond(state):
    print("evaluating condition")



# define graph
graph.add_node("a", a)
graph.add_node("b", b)
graph.add_node("c", c)
graph.add_node("d", d)
graph.add_node("e", e)
# graph.add_node("f", f)

graph.add_edge("a", "b")
graph.add_edge("b", "c")
# graph.add_edge("c", "d")
graph.add_edge("d", "c")

graph.add_conditional_edges("c", cond, path_map=["e", "d"])



graph.set_entry_point("a")
graph.set_finish_point("e")

runnable = graph.compile()

# draw graph
image_data = runnable.get_graph().draw_mermaid_png(
    draw_method=MermaidDrawMethod.API,
)

# Define the file path where you want to save the image
file_path = "sample_graph.png"

# Open the file in binary write mode and write the image data
with open(file_path, "wb") as file:
    file.write(image_data)


response = runnable.invoke({
    "text": [],
    "b": [],
    "review_count": 0
}, {"recursion_limit": 20})
