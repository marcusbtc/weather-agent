"""O Grafo: nó de modelo ↔ nó de tools (AC-03).

Se o modelo pede uma Tool, vai para `tools` e volta para `model`; quando não pede,
termina. O modelo é injetado para o Grafo ser testável sem OpenAI.
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from weather_agent.tools import TOOLS

SYSTEM_PROMPT = (
    "You are a weather assistant. To answer about a city's weather, call the get_weather "
    "tool, then reply in one sentence, in the user's language, stating the temperature "
    "in °C and the condition exactly as the tool returned them."
)


def build_graph(model: BaseChatModel) -> CompiledStateGraph:
    model_with_tools = model.bind_tools(TOOLS)

    async def call_model(state: MessagesState) -> dict:
        messages = [SystemMessage(SYSTEM_PROMPT), *state["messages"]]
        response = await model_with_tools.ainvoke(messages)
        return {"messages": [response]}

    graph = StateGraph(MessagesState)
    graph.add_node("model", call_model)
    graph.add_node("tools", ToolNode(TOOLS))

    graph.add_edge(START, "model")
    graph.add_conditional_edges("model", tools_condition, {"tools": "tools", END: END})
    graph.add_edge("tools", "model")

    return graph.compile()
