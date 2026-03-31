import { describe, expect, it } from "vitest";
import { filterWebSearchToolMessages } from "./messageVisibility";

describe("filterWebSearchToolMessages", () => {
  it("hides tool messages produced by web_search", () => {
    const messages: any[] = [
      { type: "human", content: "天气" },
      {
        type: "ai",
        content: "",
        tool_calls: [{ name: "web_search", args: { query: "天气" }, id: "c1" }],
      },
      { type: "tool", content: "- r1 [t](u)", tool_call_id: "c1" },
      { type: "ai", content: "最终回答" },
    ];

    expect(filterWebSearchToolMessages(messages)).toEqual([
      messages[0],
      messages[1],
      messages[3],
    ]);
  });

  it("does not hide tool messages for other tools", () => {
    const messages: any[] = [
      { type: "human", content: "topic" },
      {
        type: "ai",
        content: "",
        tool_calls: [
          {
            name: "handoff_research",
            args: { query: "topic", effort: "medium", model: "qwen-plus" },
            id: "c2",
          },
        ],
      },
      { type: "tool", content: "进入研究流程。", tool_call_id: "c2" },
      { type: "ai", content: "最终回答" },
    ];

    expect(filterWebSearchToolMessages(messages)).toEqual(messages);
  });

  it("keeps tool messages when tool_call_id is missing or unmapped", () => {
    const messages: any[] = [
      { type: "ai", content: "", tool_calls: [{ name: "web_search", id: "c1" }] },
      { type: "tool", content: "x" },
      { type: "tool", content: "y", tool_call_id: "unknown" },
    ];

    expect(filterWebSearchToolMessages(messages)).toEqual(messages);
  });

  it("supports camelCase fields from SDK", () => {
    const messages: any[] = [
      {
        type: "ai",
        content: "",
        toolCalls: [{ name: "web_search", args: { query: "q" }, id: "c1" }],
      },
      { type: "tool", content: "x", toolCallId: "c1" },
      { type: "ai", content: "ok" },
    ];

    expect(filterWebSearchToolMessages(messages)).toEqual([messages[0], messages[2]]);
  });
});

