import { useStream } from "@langchain/langgraph-sdk/react";
import type { Message } from "@langchain/langgraph-sdk";
import { useState, useEffect, useRef, useCallback } from "react";
import { ProcessedEvent } from "@/components/ActivityTimeline";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { ChatMessagesView } from "@/components/ChatMessagesView";
import { Button } from "@/components/ui/button";
import {
  cloneProcessedEvents,
  upsertProcessedEvent,
} from "@/lib/activityTimeline";
import { deriveUiMode, shouldShowWebSearchIndicator, UiMode } from "@/lib/uiMode";
import { filterWebSearchToolMessages } from "@/lib/messageVisibility";

export default function App() {
  const [processedEventsTimeline, setProcessedEventsTimeline] = useState<
    ProcessedEvent[]
  >([]);
  const [historicalActivities, setHistoricalActivities] = useState<
    Record<string, ProcessedEvent[]>
  >({});
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const hasFinalizeEventOccurredRef = useRef(false);
  const shouldAcceptEventsRef = useRef(false);
  const uiModeRef = useRef<UiMode>("none");
  const [error, setError] = useState<string | null>(null);
  const [lastUpdateEvent, setLastUpdateEvent] = useState<any>(null);
  const [uiMode, setUiMode] = useState<UiMode>("none");
  const thread = useStream<{
    messages: Message[];
    effort: string;
    reasoning_model: string;
  }>({
    apiUrl: import.meta.env.DEV
      ? "http://localhost:2024"
      : "http://localhost:8123",
    assistantId: "agent",
    messagesKey: "messages",
    onUpdateEvent: (event: any) => {
      setLastUpdateEvent(event);
      let processedEvent: ProcessedEvent | null = null;
      if (event.generate_query) {
        processedEvent = {
          title: "Generating Search Queries",
          data: event.generate_query?.search_query?.join(", ") || "",
        };
      } else if (event.web_research) {
        const sources = event.web_research.sources_gathered || [];
        const numSources = sources.length;
        const uniqueLabels = [
          ...new Set(sources.map((s: any) => s.label).filter(Boolean)),
        ];
        const exampleLabels = uniqueLabels.slice(0, 3).join(", ");
        processedEvent = {
          title: "Web Research",
          data: `Gathered ${numSources} sources. Related to: ${
            exampleLabels || "N/A"
          }.`,
        };
      } else if (event.reflection) {
        processedEvent = {
          title: "Reflection",
          data: "Analysing Web Research Results",
        };
      } else if (event.finalize_answer) {
        processedEvent = {
          title: "Finalizing Answer",
          data: "Composing and presenting the final answer.",
        };
        hasFinalizeEventOccurredRef.current = true;
      }
      if (processedEvent) {
        if (!shouldAcceptEventsRef.current) return;
        setProcessedEventsTimeline((prevEvents) =>
          upsertProcessedEvent(prevEvents, processedEvent!)
        );
      }
    },
    onError: (error: any) => {
      setError(error.message);
    },
  });

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollViewport = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollViewport) {
        scrollViewport.scrollTop = scrollViewport.scrollHeight;
      }
    }
  }, [thread.messages]);

  useEffect(() => {
    if (
      hasFinalizeEventOccurredRef.current &&
      !thread.isLoading &&
      thread.messages.length > 0
    ) {
      const lastMessage = thread.messages[thread.messages.length - 1];
      if (lastMessage && lastMessage.type === "ai" && lastMessage.id) {
        setHistoricalActivities((prev) => ({
          ...prev,
          [lastMessage.id!]: cloneProcessedEvents(processedEventsTimeline),
        }));
      }
      hasFinalizeEventOccurredRef.current = false;
      shouldAcceptEventsRef.current = false;
    }
  }, [thread.messages, thread.isLoading, processedEventsTimeline]);

  useEffect(() => {
    const nextMode = deriveUiMode({
      messages: thread.messages,
      lastEvent: lastUpdateEvent,
    });
    setUiMode(nextMode);
    uiModeRef.current = nextMode;
    shouldAcceptEventsRef.current = nextMode === "research";
  }, [thread.messages, lastUpdateEvent]);

  const handleSubmit = useCallback(
    (submittedInputValue: string, effort: string, model: string) => {
      if (!submittedInputValue.trim()) return;
      thread.stop();
      setProcessedEventsTimeline([]);
      hasFinalizeEventOccurredRef.current = false;
      shouldAcceptEventsRef.current = false;
      uiModeRef.current = "none";
      setUiMode("none");
      setLastUpdateEvent(null);

      const newMessages: Message[] = [
        ...(thread.messages || []),
        {
          type: "human",
          content: submittedInputValue,
          id: Date.now().toString(),
        },
      ];
      thread.submit({
        messages: newMessages,
        effort: effort,
        reasoning_model: model,
      });
    },
    [thread]
  );

  const handleCancel = useCallback(() => {
    thread.stop();
    window.location.reload();
  }, [thread]);

  const displayMessages = filterWebSearchToolMessages(
    thread.messages.filter((m) => {
    if (m.type === "ai" && typeof m.content === "string") {
      const cleanStr = m.content.replace(/^```json\s*/, "").trim();
      if (!cleanStr.startsWith("{")) return true;

      try {
        const parsed = JSON.parse(cleanStr);
        if (
          parsed.rationale !== undefined ||
          parsed.query !== undefined ||
          parsed.is_sufficient !== undefined
        ) {
          return false;
        }
      } catch (e) {
        if (/^\{\s*"(rationale|query|is_sufficient)/.test(cleanStr)) {
          return false;
        }
        if (cleanStr.length < 20 && /^\{\s*"?[a-z_]*"?\s*:?/.test(cleanStr)) {
          return false;
        }
      }
    }
    return true;
    })
  );

  return (
    <div className="flex h-screen bg-neutral-800 text-neutral-100 font-sans antialiased">
      <main className="h-full w-full max-w-4xl mx-auto">
          {thread.messages.length === 0 ? (
            <WelcomeScreen
              handleSubmit={handleSubmit}
              isLoading={thread.isLoading}
              onCancel={handleCancel}
            />
          ) : error ? (
            <div className="flex flex-col items-center justify-center h-full">
              <div className="flex flex-col items-center justify-center gap-4">
                <h1 className="text-2xl text-red-400 font-bold">Error</h1>
                <p className="text-red-400">{JSON.stringify(error)}</p>

                <Button
                  variant="destructive"
                  onClick={() => window.location.reload()}
                >
                  Retry
                </Button>
              </div>
            </div>
          ) : (
            <ChatMessagesView
              messages={displayMessages}
              isLoading={thread.isLoading}
              webSearchIndicator={shouldShowWebSearchIndicator({
                mode: uiMode,
                isLoading: thread.isLoading,
              })}
              scrollAreaRef={scrollAreaRef}
              onSubmit={handleSubmit}
              onCancel={handleCancel}
              liveActivityEvents={processedEventsTimeline}
              historicalActivities={historicalActivities}
            />
          )}
      </main>
    </div>
  );
}
