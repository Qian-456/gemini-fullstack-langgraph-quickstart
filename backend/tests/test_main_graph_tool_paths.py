import sys
import types

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from agent.tools_and_schemas import Reflection, SearchQueryList


@pytest.fixture()
def fake_providers(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-dashscope")
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily")

    tavily_mod = types.ModuleType("tavily")

    class FakeTavilyClient:
        def __init__(self, api_key: str):
            self.api_key = api_key

        def search(self, query: str, max_results: int, search_depth: str):
            return {
                "results": [
                    {
                        "title": "Alpha",
                        "url": "https://a",
                        "content": f"Result for: {query}",
                    }
                ]
            }

    tavily_mod.TavilyClient = FakeTavilyClient
    sys.modules["tavily"] = tavily_mod

    lc_mod = types.ModuleType("langchain_community")
    chat_models_mod = types.ModuleType("langchain_community.chat_models")

    class FakeStructured:
        def __init__(self, schema):
            self.schema = schema

        def invoke(self, prompt: str):
            if self.schema is SearchQueryList:
                return None
            if self.schema is Reflection:
                return Reflection(
                    is_sufficient=True,
                    knowledge_gap="",
                    follow_up_queries=[],
                )
            return None

    class FakeChatTongyi:
        def __init__(self, model: str, temperature: float = 0.0, max_retries: int = 0):
            self.model = model
            self.temperature = temperature
            self.max_retries = max_retries
            self._turn = 0

        def bind_tools(self, tools):
            self._tools = tools
            return self

        def with_structured_output(self, schema):
            return FakeStructured(schema)

        def invoke(self, input):
            self._turn += 1

            messages = input if isinstance(input, list) else None
            if messages:
                last_human = next(
                    (m for m in reversed(messages) if isinstance(m, HumanMessage)), None
                )
                last_tool = next(
                    (m for m in reversed(messages) if isinstance(m, ToolMessage)), None
                )

                if last_tool is not None:
                    return AIMessage(
                        content="这是最终回答（含来源）：https://a",
                    )

                text = (last_human.content if last_human else "") or ""
                if "天气" in text or "实时" in text:
                    return AIMessage(
                        content="",
                        tool_calls=[
                            {"name": "web_search", "args": {"query": text}, "id": "c1"}
                        ],
                    )
                if "严谨" in text or "报告" in text or "research" in text.lower():
                    return AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": "handoff_research",
                                "args": {"query": text, "effort": "medium", "model": "qwen-plus"},
                                "id": "c2",
                            }
                        ],
                    )
                return AIMessage(content="你好！我是 AI 助手。")

            if isinstance(input, str):
                if self.temperature != 0:
                    return types.SimpleNamespace(
                        content='{"rationale":"r","query":["q1"]}'
                    )
                return types.SimpleNamespace(
                    content="Final answer [Alpha](https://sources.local/id/0-0)"
                )

            return AIMessage(content="fallback")

    chat_models_mod.ChatTongyi = FakeChatTongyi
    lc_mod.chat_models = chat_models_mod
    sys.modules["langchain_community"] = lc_mod
    sys.modules["langchain_community.chat_models"] = chat_models_mod


def test_none_path_returns_direct_answer(fake_providers):
    from agent.graph import graph

    result = graph.invoke({"messages": [HumanMessage(content="你好")]})
    assert result["messages"][-1].content
    assert "已收到消息" not in result["messages"][-1].content


def test_web_search_path_calls_tool_and_returns_answer(fake_providers):
    from agent.graph import graph

    result = graph.invoke({"messages": [HumanMessage(content="今天北京天气怎么样？")]})
    assert "https://a" in result["messages"][-1].content


def test_research_path_handoffs_into_research_flow(fake_providers):
    from agent.graph import graph

    result = graph.invoke({"messages": [HumanMessage(content="请写一份严谨的报告：测试主题")]})
    assert result["messages"][-1].content
