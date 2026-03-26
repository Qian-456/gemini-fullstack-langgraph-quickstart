import type { ProcessedEvent } from "../components/ActivityTimeline";

export function upsertProcessedEvent(
  prev: ProcessedEvent[],
  next: ProcessedEvent,
  key: (e: ProcessedEvent) => string = (e) => e.title
): ProcessedEvent[] {
  if (prev.length === 0) return [next];

  const nextKey = key(next);
  const lastIndex = prev.length - 1;
  const lastKey = key(prev[lastIndex]);

  // If the last event is of the same type (e.g. parallel Web Research events), update it
  if (lastKey === nextKey) {
    const newPrev = [...prev];
    newPrev[lastIndex] = next;
    return newPrev;
  }

  // Otherwise, it's a new phase or a new loop, so append
  return [...prev, next];
}

export function cloneProcessedEvents(events: ProcessedEvent[]): ProcessedEvent[] {
  return events.map((e) => ({ ...e }));
}

