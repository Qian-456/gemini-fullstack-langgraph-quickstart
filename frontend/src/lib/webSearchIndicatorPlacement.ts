export function shouldShowWebSearchIndicatorAfterIndex(args: {
  messages: any[];
  index: number;
  webSearchIndicator: boolean;
  isLoading: boolean;
}): boolean {
  if (!args.webSearchIndicator) return false;
  if (!args.isLoading) return false;

  const messages = args.messages || [];
  let lastHumanIndex = -1;
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i]?.type === "human") {
      lastHumanIndex = i;
      break;
    }
  }
  if (lastHumanIndex === -1) return false;
  return args.index === lastHumanIndex;
}

