import { useState, useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { useChat } from "ai/react";
import type { Message, JSONValue } from "ai";

import { TimeRange, OpeningDataPoint } from "../features/market-health/JobOpeningsChart";
import { TopBar } from "../features/market-health/TopBar";
import { TaskPanel } from "../features/market-health/TaskPanel";
import { ConversationThread } from "../features/market-health/ConversationThread";
import { MarketBriefingMessage, OPENING_PROMPT } from "../features/market-health/MarketBriefingMessage";
import { ChatInput } from "../features/market-health/ChatInput";
import { OutputPanel } from "../features/market-health/OutputPanel";
import { ReasoningTrace } from "../components/ReasoningPanel";


interface OpeningsResponse {
  range: TimeRange;
  data: OpeningDataPoint[];
  summary: string;
  as_of: string;
  source: string;
}

interface TraceEntry {
  trace: ReasoningTrace | null;
  generationTimeMs: number | null;
}

async function fetchOpenings(range: TimeRange): Promise<OpeningsResponse> {
  const res = await fetch(`/api/market-health/openings?range=${range}`);
  if (!res.ok) throw new Error(`Failed to fetch opening trends (${res.status})`);
  return res.json();
}

export function MarketHealthPage() {
  const [range, setRange] = useState<TimeRange>("this_year");
  const [activeTaskId, setActiveTaskId] = useState("market-health");

  const openingsQuery = useQuery<OpeningsResponse, Error>({
    queryKey: ["market-health", "openings", range],
    queryFn: () => fetchOpenings(range),
    placeholderData: (prev) => prev,
  });

  // ── Briefing load time ─────────────────────────────────────────────────────
  const pageLoadRef = useRef(Date.now());
  const [briefingTimeMs, setBriefingTimeMs] = useState<number | null>(null);
  const briefingTimedRef = useRef(false);

  useEffect(() => {
    if (!openingsQuery.isLoading && !briefingTimedRef.current) {
      setBriefingTimeMs(Date.now() - pageLoadRef.current);
      briefingTimedRef.current = true;
    }
  }, [openingsQuery.isLoading]);

  // ── Briefing reasoning trace ───────────────────────────────────────────────
  const briefingTrace: ReasoningTrace | null = openingsQuery.data
    ? {
        input_context:
          `Task prompt: "${OPENING_PROMPT.slice(0, 140)}…" ` +
          `Time range: ${range}. No role, seniority, or location filters applied.`,
        sources_and_tools: [
          {
            sequence: 1,
            source_type: "data_source",
            name: "Job Openings Dataset",
            purpose:
              `Retrieve monthly opening counts for Designer, Product Manager, and Engineer ` +
              `role categories for the ${range} time range`,
          },
        ],
        reasoning_steps: [
          {
            sequence: 1,
            content:
              `Retrieved monthly job opening counts for 3 role categories (Designer, ` +
              `Product Manager, Engineer) from the Job Openings Dataset ` +
              `(${openingsQuery.data.data.length} data point${openingsQuery.data.data.length !== 1 ? "s" : ""}, ` +
              `as of ${openingsQuery.data.as_of}).`,
          },
          {
            sequence: 2,
            content:
              `Rendered the data as a multi-series line chart with time range controls ` +
              `(This Year, Past 5 Years, All Time). Each line represents one role category, ` +
              `plotted month over month.`,
          },
          {
            sequence: 3,
            content:
              `Generated a written summary describing overall market direction, magnitude of ` +
              `change, and notable differences across role categories. ` +
              `Source: ${openingsQuery.data.source}.`,
          },
        ],
        is_complete: true,
      }
    : null;

  // ── Trace state (for real chat messages) ───────────────────────────────────
  const [traces, setTraces] = useState<Map<string, TraceEntry>>(new Map());
  const pendingTrace = useRef<ReasoningTrace | null>(null);
  const pendingGenerationTime = useRef<number | null>(null);
  const processedDataCount = useRef(0);

  // ── Chat ──────────────────────────────────────────────────────────────────
  const { messages, input, handleInputChange, handleSubmit, isLoading, data } = useChat({
    api: "/api/chat",
    streamProtocol: "data",
    body: { context: { role: "all", seniority: "all", location: "all" } },
    onFinish: (message) => {
      setTraces((prev) =>
        new Map(prev).set(message.id, {
          trace: pendingTrace.current,
          generationTimeMs: pendingGenerationTime.current,
        })
      );
      pendingTrace.current = null;
      pendingGenerationTime.current = null;
    },
  });

  useEffect(() => {
    if (!data) {
      processedDataCount.current = 0;
      return;
    }
    const newItems = data.slice(processedDataCount.current);
    for (const item of newItems) {
      if (!item || typeof item !== "object") continue;
      const typed = item as Record<string, JSONValue>;
      if (typed["type"] === "reasoning_trace") {
        pendingTrace.current = typed["trace"] as unknown as ReasoningTrace;
      } else if (typed["type"] === "finish_message") {
        pendingGenerationTime.current = typed["generation_time_ms"] as number;
      }
    }
    processedDataCount.current = data.length;
  }, [data]);


  return (
    <div className="flex flex-col h-screen bg-gray-900 text-gray-100">
      {/* Full-width top bar */}
      <TopBar />

      {/* Three-column body */}
      <div className="flex flex-1 overflow-hidden">

        {/* Left — Task Panel */}
        <TaskPanel activeTaskId={activeTaskId} onSelect={setActiveTaskId} />

        {/* Centre — Working Space */}
        <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
          <ConversationThread
            messages={messages as Message[]}
            isLoading={isLoading}
            briefingTimeMs={briefingTimeMs}
            briefingTrace={briefingTrace}
            briefingIsStreaming={openingsQuery.isLoading}
            traces={traces}
            activeDemoSim={null}
          >
            <MarketBriefingMessage
              range={range}
              onRangeChange={setRange}
              data={openingsQuery.data?.data}
              summary={openingsQuery.data?.summary}
              isLoading={openingsQuery.isLoading}
              isFetching={openingsQuery.isFetching}
              error={openingsQuery.error}
              onRetry={() => openingsQuery.refetch()}
            />
          </ConversationThread>
          <ChatInput
            input={input}
            onChange={handleInputChange}
            onSubmit={handleSubmit}
            isLoading={isLoading}
          />
        </div>

        {/* Right — Output Panel */}
        <OutputPanel messages={messages as Message[]} />
      </div>
    </div>
  );
}
