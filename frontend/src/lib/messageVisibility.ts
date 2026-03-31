export function filterWebSearchToolMessages<T extends Record<string, any>>(
  messages: T[]
): T[] {
  const toolCallIdToName = new Map<string, string>();

  for (const m of messages || []) {
    const toolCalls = (m as any)?.tool_calls || (m as any)?.toolCalls || [];
    if (!Array.isArray(toolCalls) || toolCalls.length === 0) continue;
    for (const call of toolCalls) {
      const id = call?.id;
      const name = call?.name;
      if (!id || !name) continue;
      toolCallIdToName.set(String(id), String(name));
    }
  }

  return (messages || []).filter((m) => {
    if ((m as any)?.type !== "tool") return true;
    const toolCallId = (m as any)?.tool_call_id || (m as any)?.toolCallId;
    if (!toolCallId) return true;
    const toolName = toolCallIdToName.get(String(toolCallId));
    return toolName !== "web_search";
  });
}

