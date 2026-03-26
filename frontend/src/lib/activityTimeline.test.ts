import { describe, expect, it } from "vitest";
import type { ProcessedEvent } from "../components/ActivityTimeline";
import { cloneProcessedEvents, upsertProcessedEvent } from "./activityTimeline";

describe("upsertProcessedEvent", () => {
  it("appends when key not present", () => {
    const prev: ProcessedEvent[] = [{ title: "A", data: "1" }];
    const next: ProcessedEvent = { title: "B", data: "2" };
    expect(upsertProcessedEvent(prev, next)).toEqual([
      { title: "A", data: "1" },
      { title: "B", data: "2" },
    ]);
  });

  it("replaces only when the LAST item matches the key, otherwise appends", () => {
    const prev: ProcessedEvent[] = [
      { title: "Generating Search Queries", data: "q1" },
      { title: "Web Research", data: "old" },
    ];

    // Case 1: Last item matches, so it replaces
    const next1: ProcessedEvent = { title: "Web Research", data: "new" };
    expect(upsertProcessedEvent(prev, next1)).toEqual([
      { title: "Generating Search Queries", data: "q1" },
      { title: "Web Research", data: "new" },
    ]);

    // Case 2: Last item does NOT match, so it appends (simulating a new loop)
    const prev2: ProcessedEvent[] = [
      { title: "Generating Search Queries", data: "q1" },
      { title: "Web Research", data: "new" },
      { title: "Reflection", data: "r" },
    ];
    const next2: ProcessedEvent = { title: "Web Research", data: "loop2" };
    expect(upsertProcessedEvent(prev2, next2)).toEqual([
      { title: "Generating Search Queries", data: "q1" },
      { title: "Web Research", data: "new" },
      { title: "Reflection", data: "r" },
      { title: "Web Research", data: "loop2" },
    ]);
  });
});

describe("cloneProcessedEvents", () => {
  it("creates a new array and new item objects", () => {
    const input: ProcessedEvent[] = [{ title: "Web Research", data: "x" }];
    const cloned = cloneProcessedEvents(input);

    expect(cloned).toEqual(input);
    expect(cloned).not.toBe(input);
    expect(cloned[0]).not.toBe(input[0]);
  });
});

