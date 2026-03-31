import sys
import types

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from agent.tools_and_schemas import Reflection, SearchQueryList


def test_graph_invoke_e2e_with_fake_providers(monkeypatch):
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
                        "content": "Alpha snippet.",
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
        def __init__(self, model: str, temperature: float, max_retries: int):
            self.model = model
            self.temperature = temperature
            self.max_retries = max_retries

        def bind_tools(self, tools):
            self._tools = tools
            return self

        def invoke(self, prompt: str):
            if isinstance(prompt, list):
                last_tool = next(
                    (m for m in reversed(prompt) if isinstance(m, ToolMessage)), None
                )
                if last_tool is not None:
                    return AIMessage(
                        content="这是最终回答（含来源）：https://a",
                    )
                last_human = next(
                    (m for m in reversed(prompt) if isinstance(m, HumanMessage)), None
                )
                query = last_human.content if last_human else "test question"
                return AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "handoff_research",
                            "args": {"query": query, "effort": "low", "model": "qwen-plus"},
                            "id": "c_research",
                        }
                    ],
                )
            if self.temperature != 0:
                return types.SimpleNamespace(
                    content='{"rationale":"r","query":["q1"]}'
                )
            return types.SimpleNamespace(
                content="Final answer [Alpha](https://sources.local/id/0-0)"
            )

        def with_structured_output(self, schema):
            return FakeStructured(schema)

    chat_models_mod.ChatTongyi = FakeChatTongyi
    lc_mod.chat_models = chat_models_mod
    sys.modules["langchain_community"] = lc_mod
    sys.modules["langchain_community.chat_models"] = chat_models_mod

    from agent.graph import graph

    result = graph.invoke(
        {
            "messages": [HumanMessage(content="test question")],
            "initial_search_query_count": 1,
            "max_research_loops": 1,
        }
    )

    assert "https://a" in result["messages"][-1].content
    assert "https://sources.local/id/" not in result["messages"][-1].content
