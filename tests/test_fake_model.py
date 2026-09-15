import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from weather_agent.fake_model import FakeWeatherChatModel


def test_fake_model_asks_for_the_weather_tool_with_the_city_in_the_message():
    model = FakeWeatherChatModel().bind_tools([])

    response = model.invoke([SystemMessage("..."), HumanMessage("Qual o clima em Curitiba?")])

    assert isinstance(response, AIMessage)
    assert response.content == ""
    assert [(tc["name"], tc["args"]) for tc in response.tool_calls] == [
        ("get_weather", {"city": "Curitiba"})
    ]


def test_fake_model_defaults_to_sao_paulo_when_no_city_is_named():
    response = FakeWeatherChatModel().invoke([HumanMessage("e o clima?")])

    assert response.tool_calls[0]["args"] == {"city": "São Paulo"}


def test_fake_model_answers_from_the_tool_result():
    tool_result = {"city": "Curitiba, Brasil", "temp_c": 18.5, "condition": "nublado"}
    messages = [
        HumanMessage("Qual o clima em Curitiba?"),
        AIMessage(content="", tool_calls=[{"id": "call_1", "name": "get_weather", "args": {"city": "Curitiba"}}]),
        ToolMessage(content=json.dumps(tool_result), tool_call_id="call_1"),
    ]

    response = FakeWeatherChatModel().invoke(messages)

    assert response.tool_calls == []
    assert response.content == "Em Curitiba, Brasil faz 18.5°C, nublado."


async def test_fake_model_streams_the_answer_in_several_chunks():
    tool_result = {"city": "Curitiba", "temp_c": 18, "condition": "nublado"}
    messages = [
        HumanMessage("Qual o clima em Curitiba?"),
        AIMessage(content="", tool_calls=[{"id": "call_1", "name": "get_weather", "args": {"city": "Curitiba"}}]),
        ToolMessage(content=json.dumps(tool_result), tool_call_id="call_1"),
    ]

    chunks = [c async for c in FakeWeatherChatModel(token_delay=0).astream(messages)]

    assert len(chunks) > 3
    assert "".join(c.content for c in chunks) == "Em Curitiba faz 18°C, nublado."
