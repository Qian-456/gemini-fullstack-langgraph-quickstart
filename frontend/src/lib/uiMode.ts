export type UiMode = "none" | "web_search" | "research";

export function deriveUiMode(args: {
  messages: any[];
  lastEvent?: any;
}): UiMode {
  const messages = args.messages || [];

  if (args.lastEvent) {
    const e = args.lastEvent;
    if (e.generate_query || e.web_research || e.reflection || e.finalize_answer) {
      return "research";
    }
  }

  for (let i = messages.length - 1; i >= 0; i--) {
    const m = messages[i] || {};
    const toolCalls = m.tool_calls || m.toolCalls || [];
    if (!Array.isArray(toolCalls) || toolCalls.length === 0) continue;
    const names = toolCalls.map((c: any) => c?.name).filter(Boolean);
    if (names.includes("handoff_research")) return "research";
    if (names.includes("web_search")) return "web_search";
  }

  return "none";
}

export function shouldShowWebSearchIndicator(args: {
  mode: UiMode;
  isLoading: boolean;
}): boolean {
  return args.mode === "web_search" && args.isLoading;
}
