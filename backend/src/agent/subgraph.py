from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from agent.configuration import Configuration
from agent.prompts import (
    answer_instructions,
    get_current_date,
    query_writer_instructions,
    reflection_instructions,
)
from agent.state import (
    OverallState,
    QueryGenerationState,
    ReflectionState,
    WebSearchState,
)
from agent.tools_and_schemas import Reflection, SearchQueryList
from agent.utils import (
    expand_short_urls,
    get_research_topic,
    parse_json_from_text,
    require_env_var,
    tavily_results_to_research_text,
)

load_dotenv()


def generate_query(state: OverallState, config: RunnableConfig) -> QueryGenerationState:
    """Generate search queries based on the user's question."""
    configurable = Configuration.from_runnable_config(config)

    if state.get("initial_search_query_count") is None:
        state["initial_search_query_count"] = configurable.number_of_initial_queries

    require_env_var("DASHSCOPE_API_KEY")
    from langchain_community.chat_models import ChatTongyi

    llm = ChatTongyi(
        model=configurable.query_generator_model,
        temperature=1.0,
        max_retries=2,
    )
    structured_llm = llm.with_structured_output(SearchQueryList)

    current_date = get_current_date()
    formatted_prompt = query_writer_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        number_queries=state["initial_search_query_count"],
    )
    try:
        result = structured_llm.invoke(formatted_prompt)
    except Exception:
        result = None

    if result is None:
        raw = llm.invoke(formatted_prompt)
        parsed = parse_json_from_text(raw.content)
        queries = parsed.get("query", [])
        if isinstance(queries, str):
            queries = [queries]
        if not isinstance(queries, list) or not queries:
            queries = [get_research_topic(state["messages"])]
        return {"search_query": queries[: state["initial_search_query_count"]]}

    return {"search_query": result.query}


def continue_to_web_research(state: QueryGenerationState):
    """Spawn n web research nodes, one for each search query."""
    return [
        Send("web_research", {"search_query": search_query, "id": int(idx)})
        for idx, search_query in enumerate(state["search_query"])
    ]


def web_research(state: WebSearchState, config: RunnableConfig) -> OverallState:
    """Perform web research using Tavily Search."""
    require_env_var("TAVILY_API_KEY")
    from tavily import TavilyClient

    client = TavilyClient(api_key=require_env_var("TAVILY_API_KEY"))
    search = client.search(
        query=state["search_query"],
        max_results=5,
        search_depth="advanced",
    )
    results = search.get("results", [])
    modified_text, sources_gathered = tavily_results_to_research_text(
        results=results,
        id=state["id"],
    )

    return {
        "sources_gathered": sources_gathered,
        "search_query": [state["search_query"]],
        "web_research_result": [modified_text],
    }


def reflection(state: OverallState, config: RunnableConfig) -> ReflectionState:
    """Identify knowledge gaps and generate potential follow-up queries."""
    configurable = Configuration.from_runnable_config(config)
    state["research_loop_count"] = state.get("research_loop_count", 0) + 1
    reasoning_model = state.get("reasoning_model", configurable.reflection_model)

    current_date = get_current_date()
    formatted_prompt = reflection_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        summaries="\n\n---\n\n".join(state["web_research_result"]),
    )

    require_env_var("DASHSCOPE_API_KEY")
    from langchain_community.chat_models import ChatTongyi

    llm = ChatTongyi(
        model=reasoning_model,
        temperature=1.0,
        max_retries=2,
    )
    structured_llm = llm.with_structured_output(Reflection)
    try:
        result = structured_llm.invoke(formatted_prompt)
    except Exception:
        result = None

    if result is None:
        raw = llm.invoke(formatted_prompt)
        parsed = parse_json_from_text(raw.content)
        is_sufficient = bool(parsed.get("is_sufficient", False))
        knowledge_gap = str(parsed.get("knowledge_gap", ""))
        follow_up_queries = parsed.get("follow_up_queries", [])
        if isinstance(follow_up_queries, str):
            follow_up_queries = [follow_up_queries]
        if not isinstance(follow_up_queries, list):
            follow_up_queries = []
        return {
            "is_sufficient": is_sufficient,
            "knowledge_gap": knowledge_gap if not is_sufficient else "",
            "follow_up_queries": follow_up_queries if not is_sufficient else [],
            "research_loop_count": state["research_loop_count"],
            "number_of_ran_queries": len(state["search_query"]),
        }

    return {
        "is_sufficient": result.is_sufficient,
        "knowledge_gap": result.knowledge_gap,
        "follow_up_queries": result.follow_up_queries,
        "research_loop_count": state["research_loop_count"],
        "number_of_ran_queries": len(state["search_query"]),
    }


def evaluate_research(
    state: ReflectionState,
    config: RunnableConfig,
) -> OverallState:
    """Determine whether to continue research or finalize the answer."""
    configurable = Configuration.from_runnable_config(config)
    max_research_loops = (
        state.get("max_research_loops")
        if state.get("max_research_loops") is not None
        else configurable.max_research_loops
    )
    if state["is_sufficient"] or state["research_loop_count"] >= max_research_loops:
        return "finalize_answer"
    return [
        Send(
            "web_research",
            {
                "search_query": follow_up_query,
                "id": state["number_of_ran_queries"] + int(idx),
            },
        )
        for idx, follow_up_query in enumerate(state["follow_up_queries"])
    ]


def finalize_answer(state: OverallState, config: RunnableConfig):
    """Compose and present the final answer with citations."""
    configurable = Configuration.from_runnable_config(config)
    reasoning_model = state.get("reasoning_model") or configurable.answer_model

    current_date = get_current_date()
    formatted_prompt = answer_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        summaries="\n---\n\n".join(state["web_research_result"]),
    )

    require_env_var("DASHSCOPE_API_KEY")
    from langchain_community.chat_models import ChatTongyi

    llm = ChatTongyi(
        model=reasoning_model,
        temperature=0,
        max_retries=2,
    )
    result = llm.invoke(formatted_prompt)
    expanded_text, used_sources = expand_short_urls(
        result.content, state["sources_gathered"]
    )

    return {
        "messages": [AIMessage(content=expanded_text)],
        "sources_gathered": used_sources,
    }


builder = StateGraph(OverallState, config_schema=Configuration)
builder.add_node("generate_query", generate_query)
builder.add_node("web_research", web_research)
builder.add_node("reflection", reflection)
builder.add_node("finalize_answer", finalize_answer)

builder.add_edge(START, "generate_query")
builder.add_conditional_edges(
    "generate_query", continue_to_web_research, ["web_research"]
)
builder.add_edge("web_research", "reflection")
builder.add_conditional_edges(
    "reflection", evaluate_research, ["web_research", "finalize_answer"]
)
builder.add_edge("finalize_answer", END)

subgraph = builder.compile(name="research-subgraph")

