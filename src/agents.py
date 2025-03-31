from typing import Literal, Annotated, Sequence

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Command
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.graph.message import add_messages
from src.prompts import supervisor_prompt
from typing_extensions import TypedDict

from flask import current_app

agents = ["rag", "dbquery"]

class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""
    next: Literal["rag", "dbquery", "FINISH"]

class AgentState(TypedDict):
    """The state of the agent."""
    messages: Annotated[Sequence[BaseMessage], add_messages]

def create_agent(llm, tools):
    llm_with_tools = llm.bind_tools(tools)
    def chatbot(state: AgentState):
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    tool_node = ToolNode(tools=tools)

    builder = StateGraph(AgentState)
    builder.add_node("agent", chatbot)
    builder.add_node("tools", tool_node)
    builder.add_conditional_edges(
        "agent",
        tools_condition,
    )
    builder.add_edge("tools", "agent")
    builder.set_entry_point("agent")
    return builder.compile()
def supervisor(state: MessagesState) -> Command[Literal["rag", "dbquery", "__end__"]]:
    agent_names_str = ", ".join(agents)
    formatted_supervisor_prompt = supervisor_prompt.format(agents=agent_names_str)
    messages = [
        {"role": "system", "content": formatted_supervisor_prompt},
    ] + state["messages"]
    response = current_app.llm.with_structured_output(Router).invoke(messages)
    goto = response["next"]
    if goto == "FINISH":
        goto = END
    return Command(goto=goto)

def rag(state: MessagesState) -> Command[Literal["supervisor"]]:
    result = current_app.rag_agent.invoke(state)
    return Command(
        update={"messages": [
            HumanMessage(content=result["messages"][-1].content, name="rag"),
        ]},
        goto="supervisor",
    )

def dbquery(state: MessagesState) -> Command[Literal["supervisor"]]:
    result = current_app.dbquery_agent.invoke(state)
    return Command(
        update={"messages": [
            HumanMessage(content=result["messages"][-1].content, name="dbquery"),
        ]},
        goto="supervisor",
    )

def setup_graph():
    builder = StateGraph(MessagesState)
    builder.add_edge(START, "supervisor")
    builder.add_node("supervisor", supervisor)
    builder.add_node("rag", rag)
    builder.add_node("dbquery", dbquery)
    return builder.compile()