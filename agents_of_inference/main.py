print("### Agents of Inference ###")

import os
from typing import TypedDict

import langgraph
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph

os.environ["OPENAI_API_KEY"] = "None"
model = ChatOpenAI(model="gpt-4", base_url="http://192.168.5.96:5001/v1")

class MyState(TypedDict):
    foo: str = None

# define state
graph = StateGraph(MyState)

def node_a(state):
    print("running node a")
    state["foo"] = "a"
    return state

def node_b(state):
    print("running node b")
    print(f"state: {state}")
    state["foo"] = "b"
    return state

# define graph
graph.add_node("a", node_a)
graph.add_node("b", node_b)


graph.add_edge("a", "b")


graph.set_entry_point("a")
graph.set_finish_point("b")

runnable = graph.compile()

test = runnable.invoke({"foo": ""})

print(test)