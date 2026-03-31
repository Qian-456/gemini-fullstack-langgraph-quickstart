import { describe, expect, it } from "vitest";
import { shouldShowWebSearchIndicatorAfterIndex } from "./webSearchIndicatorPlacement";

describe("shouldShowWebSearchIndicatorAfterIndex", () => {
  it("shows only after the last human message when enabled", () => {
    const messages: any[] = [
      { type: "human", content: "q1" },
      { type: "ai", content: "", tool_calls: [{ name: "web_search", id: "c1" }] },
      { type: "tool", content: "x", tool_call_id: "c1" },
      { type: "ai", content: "final" },
    ];

    expect(
      shouldShowWebSearchIndicatorAfterIndex({
        messages,
        index: 0,
        webSearchIndicator: true,
        isLoading: true,
      })
    ).toBe(true);

    expect(
      shouldShowWebSearchIndicatorAfterIndex({
        messages,
        index: 1,
        webSearchIndicator: true,
        isLoading: true,
      })
    ).toBe(false);
  });

  it("does not show when disabled or not loading", () => {
    const messages: any[] = [{ type: "human", content: "q1" }];

    expect(
      shouldShowWebSearchIndicatorAfterIndex({
        messages,
        index: 0,
        webSearchIndicator: false,
        isLoading: true,
      })
    ).toBe(false);

    expect(
      shouldShowWebSearchIndicatorAfterIndex({
        messages,
        index: 0,
        webSearchIndicator: true,
        isLoading: false,
      })
    ).toBe(false);
  });

  it("returns false when there is no human message", () => {
    const messages: any[] = [{ type: "ai", content: "x" }];

    expect(
      shouldShowWebSearchIndicatorAfterIndex({
        messages,
        index: 0,
        webSearchIndicator: true,
        isLoading: true,
      })
    ).toBe(false);
  });
});

