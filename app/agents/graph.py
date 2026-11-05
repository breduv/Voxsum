from functools import partial

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.nodes import call_model


def build_graph(model: BaseChatModel) -> CompiledStateGraph:
    assistant = partial(call_model, model=model)

    builder = StateGraph(MessagesState)
    builder.add_node("assistant", assistant)

    builder.add_edge(START, "assistant")
    builder.add_edge("assistant", END)

    return builder.compile()
