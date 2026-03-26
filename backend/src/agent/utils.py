import json
import os
import re
from typing import Any, Dict, Iterable, List, Tuple
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage


def get_research_topic(messages: List[AnyMessage]) -> str:
    """
    Get the research topic from the messages.
    """
    # check if request has a history and combine the messages into a single string
    if len(messages) == 1:
        research_topic = messages[-1].content
    else:
        research_topic = ""
        for message in messages:
            if isinstance(message, HumanMessage):
                research_topic += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                research_topic += f"Assistant: {message.content}\n"
    return research_topic


def require_env_var(name: str) -> str:
    """
    Read a required environment variable.

    Args:
        name: Environment variable name.

    Returns:
        The environment variable value.

    Raises:
        ValueError: If the environment variable is missing or empty.
    """
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise ValueError(f"{name} is not set")
    return value


def parse_json_from_text(text: str) -> Dict[str, Any]:
    """
    Parse a JSON object embedded in a text response.

    Args:
        text: A text response that contains a JSON object.

    Returns:
        A parsed JSON dict.

    Raises:
        ValueError: If no JSON object can be parsed from the input text.
    """
    if text is None:
        raise ValueError("No text provided for JSON parsing")

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("No JSON object found in text")

    candidate = match.group(0)
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as e:
        raise ValueError("Failed to parse JSON object from text") from e
    if not isinstance(parsed, dict):
        raise ValueError("Parsed JSON is not an object")
    return parsed


def resolve_urls(urls_to_resolve: Iterable[Any], id: int) -> Dict[str, str]:
    """
    Create a stable map of long source URLs to short placeholder URLs.

    The mapping is deterministic and deduplicates by first appearance to preserve stable
    short URL indices across runs.

    Args:
        urls_to_resolve: Iterable of URL strings or objects with a `.web.uri` attribute.
        id: A numeric identifier used to namespace the short URLs.

    Returns:
        A dict mapping each unique original URL to a short placeholder URL.
    """
    prefix = "https://sources.local/id/"

    urls: List[str] = []
    for item in urls_to_resolve:
        if isinstance(item, str):
            urls.append(item)
            continue
        try:
            urls.append(item.web.uri)
        except AttributeError:
            continue

    # Create a dictionary that maps each unique URL to a stable index based on first appearance.
    resolved_map: Dict[str, str] = {}
    for url in urls:
        if url not in resolved_map:
            resolved_map[url] = f"{prefix}{id}-{len(resolved_map)}"

    return resolved_map


def tavily_results_to_research_text(
    results: List[Dict[str, Any]],
    id: int,
) -> Tuple[str, List[Dict[str, str]]]:
    """
    Convert Tavily search results into a markdown research artifact with sources.

    Args:
        results: Tavily `results` list items containing at least `title`, `url`, and `content`.
        id: A numeric identifier used to namespace the short URLs.

    Returns:
        A tuple of:
        - research_text: Markdown text that embeds source links using short URLs.
        - sources: A list of source objects with keys: `label`, `short_url`, and `value`.
    """
    urls = [r.get("url") for r in results if r.get("url")]
    resolved_urls = resolve_urls(urls, id=id)

    sources: List[Dict[str, str]] = []
    seen_urls: set[str] = set()
    for r in results:
        url = r.get("url")
        title = (r.get("title") or "source").strip()
        if not url or url not in resolved_urls:
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)
        sources.append(
            {"label": title, "short_url": resolved_urls[url], "value": url}
        )

    lines: List[str] = []
    for r in results:
        url = r.get("url")
        if not url or url not in resolved_urls:
            continue
        title = (r.get("title") or "source").strip()
        content = (r.get("content") or "").strip()
        if content:
            lines.append(f"- {content} [{title}]({resolved_urls[url]})")
        else:
            lines.append(f"- [{title}]({resolved_urls[url]})")

    return "\n".join(lines), sources


def expand_short_urls(
    text: str,
    sources: List[Dict[str, str]],
) -> Tuple[str, List[Dict[str, str]]]:
    """
    Expand short placeholder URLs in text to their original values.

    Args:
        text: Text containing short placeholder URLs.
        sources: Source objects containing `short_url` and `value`.

    Returns:
        A tuple of:
        - expanded_text: Text with short URLs replaced by full URLs.
        - used_sources: Sources whose short URLs were present in the input text.
    """
    expanded_text = text
    used_sources: List[Dict[str, str]] = []

    for source in sources:
        short_url = source.get("short_url")
        value = source.get("value")
        if not short_url or not value:
            continue
        if short_url in expanded_text:
            expanded_text = expanded_text.replace(short_url, value)
            used_sources.append(source)

    return expanded_text, used_sources


def insert_citation_markers(text, citations_list):
    """
    Inserts citation markers into a text string based on start and end indices.

    Args:
        text (str): The original text string.
        citations_list (list): A list of dictionaries, where each dictionary
                               contains 'start_index', 'end_index', and
                               'segment_string' (the marker to insert).
                               Indices are assumed to be for the original text.

    Returns:
        str: The text with citation markers inserted.
    """
    # Sort citations by end_index in descending order.
    # If end_index is the same, secondary sort by start_index descending.
    # This ensures that insertions at the end of the string don't affect
    # the indices of earlier parts of the string that still need to be processed.
    sorted_citations = sorted(
        citations_list, key=lambda c: (c["end_index"], c["start_index"]), reverse=True
    )

    modified_text = text
    for citation_info in sorted_citations:
        # These indices refer to positions in the *original* text,
        # but since we iterate from the end, they remain valid for insertion
        # relative to the parts of the string already processed.
        end_idx = citation_info["end_index"]
        marker_to_insert = ""
        for segment in citation_info["segments"]:
            marker_to_insert += f" [{segment['label']}]({segment['short_url']})"
        # Insert the citation marker at the original end_idx position
        modified_text = (
            modified_text[:end_idx] + marker_to_insert + modified_text[end_idx:]
        )

    return modified_text


def get_citations(response, resolved_urls_map):
    """
    Extract and format citation information from a model response.

    This function processes the grounding metadata provided in the response to
    construct a list of citation objects. Each citation object includes the
    start and end indices of the text segment it refers to, and a string
    containing formatted markdown links to the supporting web chunks.

    Args:
        response: The response object from the model, expected to have
                  a structure including `candidates[0].grounding_metadata`.
                  It also relies on a `resolved_map` being available in its
                  scope to map chunk URIs to resolved URLs.

    Returns:
        list: A list of dictionaries, where each dictionary represents a citation
              and has the following keys:
              - "start_index" (int): The starting character index of the cited
                                     segment in the original text. Defaults to 0
                                     if not specified.
              - "end_index" (int): The character index immediately after the
                                   end of the cited segment (exclusive).
              - "segments" (list[str]): A list of individual markdown-formatted
                                        links for each grounding chunk.
              - "segment_string" (str): A concatenated string of all markdown-
                                        formatted links for the citation.
              Returns an empty list if no valid candidates or grounding supports
              are found, or if essential data is missing.
    """
    citations = []

    # Ensure response and necessary nested structures are present
    if not response or not response.candidates:
        return citations

    candidate = response.candidates[0]
    if (
        not hasattr(candidate, "grounding_metadata")
        or not candidate.grounding_metadata
        or not hasattr(candidate.grounding_metadata, "grounding_supports")
    ):
        return citations

    for support in candidate.grounding_metadata.grounding_supports:
        citation = {}

        # Ensure segment information is present
        if not hasattr(support, "segment") or support.segment is None:
            continue  # Skip this support if segment info is missing

        start_index = (
            support.segment.start_index
            if support.segment.start_index is not None
            else 0
        )

        # Ensure end_index is present to form a valid segment
        if support.segment.end_index is None:
            continue  # Skip if end_index is missing, as it's crucial

        # Add 1 to end_index to make it an exclusive end for slicing/range purposes
        # (assuming the API provides an inclusive end_index)
        citation["start_index"] = start_index
        citation["end_index"] = support.segment.end_index

        citation["segments"] = []
        if (
            hasattr(support, "grounding_chunk_indices")
            and support.grounding_chunk_indices
        ):
            for ind in support.grounding_chunk_indices:
                try:
                    chunk = candidate.grounding_metadata.grounding_chunks[ind]
                    resolved_url = resolved_urls_map.get(chunk.web.uri, None)
                    citation["segments"].append(
                        {
                            "label": chunk.web.title.split(".")[:-1][0],
                            "short_url": resolved_url,
                            "value": chunk.web.uri,
                        }
                    )
                except (IndexError, AttributeError, NameError):
                    # Handle cases where chunk, web, uri, or resolved_map might be problematic
                    # For simplicity, we'll just skip adding this particular segment link
                    # In a production system, you might want to log this.
                    pass
        citations.append(citation)
    return citations
