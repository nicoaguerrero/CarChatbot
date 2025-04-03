from typing import Annotated

from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages

from flask import current_app

class State(TypedDict):
    messages: Annotated[list, add_messages]

def setup_graph():
    tools = current_app.tools
    llm_with_tools = current_app.llm.bind_tools(tools)
    checkpointer = current_app.checkpointer

    def chatbot(state: State):
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    graph = StateGraph(State)
    graph.add_node("chatbot", chatbot)
    tool_node = ToolNode(tools=tools)
    graph.add_node("tools", tool_node)
    graph.add_conditional_edges(
        "chatbot",
        tools_condition
    )
    graph.add_edge("tools", "chatbot")
    graph.set_entry_point("chatbot")
    return graph.compile(checkpointer=checkpointer)
