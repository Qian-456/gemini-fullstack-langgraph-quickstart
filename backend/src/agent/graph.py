from __future__ import annotations

import json
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt.tool_node import tools_condition
from langgraph.types import Command

from agent.configuration import Configuration
from agent.state import OverallState
from agent.subgraph import (
    continue_to_web_research,
    evaluate_research,
    finalize_answer,
    generate_query,
    reflection,
    web_research,
)
from agent.utils import require_env_var
from agent.prompts import agent_system_prompt_template

load_dotenv()





@tool("web_search")
def web_search_tool(query: str) -> str:
    """使用 Web Search 获取相对实时信息。"""
    return query


@tool("handoff_research")
def handoff_research_tool(
    query: str,
    effort: str = "medium",
    model: str = "qwen-plus",
) -> str:
    """进入研究子流程，参数包含 query、effort、model。"""
    return json.dumps({"query": query, "effort": effort, "model": model}, ensure_ascii=False)


def _effort_to_limits(effort: str) -> tuple[int, int]:
    effort = (effort or "medium").lower()
    if effort == "low":
        return 1, 1
    if effort == "high":
        return 5, 10
    return 3, 3


def agent_node(state: OverallState, config: RunnableConfig) -> dict[str, Any]:
    """Call the tool-calling agent model and append its message to state."""
    configurable = Configuration.from_runnable_config(config)
    require_env_var("DASHSCOPE_API_KEY")
    from langchain_community.chat_models import ChatTongyi

    llm = ChatTongyi(
        model=configurable.reflection_model,
        temperature=0.2,
        max_retries=2,
    ).bind_tools([web_search_tool, handoff_research_tool])

    default_effort = state.get("effort") or "medium"
    default_model = state.get("reasoning_model") or configurable.reflection_model
    system_prompt = agent_system_prompt_template.format(
        default_effort=default_effort,
        default_model=default_model,
    )
    messages = [SystemMessage(content=system_prompt), *state["messages"]]
    ai: AIMessage = llm.invoke(messages)
    return {"messages": [ai]}


def tools_node(state: OverallState, config: RunnableConfig):
    """Execute tool calls from the last AI message."""
    last = state["messages"][-1]
    tool_calls = getattr(last, "tool_calls", []) or []
    if not tool_calls:
        return {"messages": []}

    call = tool_calls[0]
    name = call.get("name")
    args = call.get("args") or {}
    tool_call_id = call.get("id") or "tool_call"

    if name == "web_search":
        require_env_var("TAVILY_API_KEY")
        from tavily import TavilyClient

        query = str(args.get("query") or "")
        client = TavilyClient(api_key=require_env_var("TAVILY_API_KEY"))
        search = client.search(
            query=query,
            max_results=5,
            search_depth="advanced",
        )
        results = search.get("results", [])
        lines = []
        for r in results:
            url = r.get("url")
            title = (r.get("title") or "source").strip()
            content = (r.get("content") or "").strip()
            if not url:
                continue
            if content:
                lines.append(f"- {content} [{title}]({url})")
            else:
                lines.append(f"- [{title}]({url})")
        content = "\n".join(lines) if lines else "未找到可用的搜索结果。"
        return {"messages": [ToolMessage(content=content, tool_call_id=tool_call_id)]}

    if name == "handoff_research":
        query = str(args.get("query") or "")
        effort = str(args.get("effort") or "medium")
        model = str(args.get("model") or "qwen-plus")
        initial_search_query_count, max_research_loops = _effort_to_limits(effort)

        update: dict[str, Any] = {
            "messages": [ToolMessage(content="进入研究流程。", tool_call_id=tool_call_id)],
            "initial_search_query_count": initial_search_query_count,
            "max_research_loops": max_research_loops,
            "reasoning_model": model,
            "research_loop_count": 0,
            "search_query": [],
            "web_research_result": [],
            "sources_gathered": [],
        }
        if query:
            update["search_query"] = []
        return Command(goto="generate_query", update=update)

    return {
        "messages": [
            ToolMessage(
                content=f"不支持的工具：{name}",
                tool_call_id=tool_call_id,
                status="error",
            )
        ]
    }


builder = StateGraph(OverallState, config_schema=Configuration)

builder.add_node("agent", agent_node)
builder.add_node("tools", tools_node)

builder.add_node("generate_query", generate_query)
builder.add_node("web_research", web_research)
builder.add_node("reflection", reflection)
builder.add_node("finalize_answer", finalize_answer)

builder.add_edge(START, "agent")
builder.add_conditional_edges(
    "agent",
    tools_condition,
    {"tools": "tools", "__end__": END},
)
builder.add_edge("tools", "agent")

builder.add_conditional_edges(
    "generate_query", continue_to_web_research, ["web_research"]
)
builder.add_edge("web_research", "reflection")
builder.add_conditional_edges(
    "reflection", evaluate_research, ["web_research", "finalize_answer"]
)
builder.add_edge("finalize_answer", END)

graph = builder.compile(name="agent-main-graph")
