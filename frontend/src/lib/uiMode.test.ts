import { describe, expect, it } from "vitest";
import { deriveUiMode, shouldShowWebSearchIndicator } from "./uiMode";

describe("deriveUiMode", () => {
  it("returns none when no tool usage observed", () => {
    expect(deriveUiMode({ messages: [{ type: "human", content: "你好" }] })).toBe(
      "none"
    );
  });

  it("returns web_search when web_search tool call observed", () => {
    expect(
      deriveUiMode({
        messages: [
          { type: "human", content: "天气" },
          {
            type: "ai",
            content: "",
            tool_calls: [{ name: "web_search", args: { query: "天气" }, id: "c1" }],
          },
        ],
      })
    ).toBe("web_search");
  });

  it("returns research when handoff_research tool call observed", () => {
    expect(
      deriveUiMode({
        messages: [
          { type: "human", content: "严谨报告" },
          {
            type: "ai",
            content: "",
            tool_calls: [
              {
                name: "handoff_research",
                args: { query: "严谨报告", effort: "medium", model: "qwen-plus" },
                id: "c2",
              },
            ],
          },
        ],
      })
    ).toBe("research");
  });

  it("returns research when research-node event observed", () => {
    expect(
      deriveUiMode({
        messages: [{ type: "human", content: "topic" }],
        lastEvent: { generate_query: { search_query: ["q1"] } },
      })
    ).toBe("research");
  });
});

describe("shouldShowWebSearchIndicator", () => {
  it("shows indicator only during loading in web_search mode", () => {
    expect(shouldShowWebSearchIndicator({ mode: "web_search", isLoading: true })).toBe(
      true
    );
    expect(
      shouldShowWebSearchIndicator({ mode: "web_search", isLoading: false })
    ).toBe(false);
    expect(shouldShowWebSearchIndicator({ mode: "none", isLoading: true })).toBe(
      false
    );
    expect(shouldShowWebSearchIndicator({ mode: "research", isLoading: true })).toBe(
      false
    );
  });
});

