import pytest

from agent.utils import (
    expand_short_urls,
    parse_json_from_text,
    require_env_var,
    resolve_urls,
    tavily_results_to_research_text,
)


def test_resolve_urls_deduplicates_and_is_stable():
    resolved = resolve_urls(
        [
            "https://example.com/a",
            "https://example.com/a",
            "https://example.com/b",
        ],
        id=7,
    )

    assert list(resolved.keys()) == ["https://example.com/a", "https://example.com/b"]
    assert resolved["https://example.com/a"].endswith("/7-0")
    assert resolved["https://example.com/b"].endswith("/7-1")


def test_tavily_results_to_research_text_includes_markdown_sources():
    results = [
        {
            "title": "Alpha",
            "url": "https://example.com/a",
            "content": "Alpha snippet.",
        },
        {
            "title": "Beta",
            "url": "https://example.com/b",
            "content": "Beta snippet.",
        },
    ]

    text, sources = tavily_results_to_research_text(results=results, id=3)

    assert "Alpha snippet." in text
    assert "Beta snippet." in text
    assert "[Alpha](" in text
    assert "[Beta](" in text
    assert len(sources) == 2
    assert {s["value"] for s in sources} == {"https://example.com/a", "https://example.com/b"}


def test_expand_short_urls_replaces_only_used_sources():
    sources = [
        {"label": "Alpha", "short_url": "https://sources.local/id/1-0", "value": "https://a"},
        {"label": "Beta", "short_url": "https://sources.local/id/1-1", "value": "https://b"},
    ]

    text = "See [Alpha](https://sources.local/id/1-0)."
    expanded, used_sources = expand_short_urls(text, sources)

    assert expanded == "See [Alpha](https://a)."
    assert used_sources == [sources[0]]


def test_require_env_var_raises_when_missing(monkeypatch):
    monkeypatch.delenv("SOME_MISSING_KEY", raising=False)
    with pytest.raises(ValueError, match="SOME_MISSING_KEY is not set"):
        require_env_var("SOME_MISSING_KEY")


def test_parse_json_from_text_extracts_object_from_text():
    text = 'prefix {"a": 1, "b": ["x"]} suffix'
    assert parse_json_from_text(text) == {"a": 1, "b": ["x"]}
