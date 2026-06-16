import { useState, useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { useChat } from "ai/react";
import type { Message } from "ai";

import { MarketHealthSignalData } from "../features/market-health/MarketHealthSignal";
import { SearchImplicationData } from "../features/market-health/SearchImplication";
import { Filters } from "../features/market-health/FilterControls";
import { TrendsData } from "../features/market-health/TrendGrid";
import { ProvenanceData } from "../features/market-health/ProvenancePanel";
import { TopBar } from "../features/market-health/TopBar";
import { ConversationThread } from "../features/market-health/ConversationThread";
import { MarketBriefingMessage } from "../features/market-health/MarketBriefingMessage";
import { ChatInput } from "../features/market-health/ChatInput";

interface SummaryResponse {
  signal: MarketHealthSignalData | null;
  implication: SearchImplicationData | null;
}

const DEFAULT_FILTERS: Filters = {
  role: "all",
  seniority: "all",
  location: "all",
  period: "6m",
};

async function fetchSummary(filters: Filters): Promise<SummaryResponse> {
  const params = new URLSearchParams();
  if (filters.role !== "all") params.set("role", filters.role);
  if (filters.seniority !== "all") params.set("seniority", filters.seniority);
  if (filters.location !== "all") params.set("location", filters.location);
  const res = await fetch(`/api/market-health/summary?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch market summary (${res.status})`);
  return res.json();
}

async function fetchTrends(filters: Filters): Promise<TrendsData> {
  const params = new URLSearchParams();
  if (filters.role !== "all") params.set("role", filters.role);
  if (filters.seniority !== "all") params.set("seniority", filters.seniority);
  if (filters.location !== "all") params.set("location", filters.location);
  params.set("period", filters.period);
  const res = await fetch(`/api/market-health/trends?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch trend data (${res.status})`);
  return res.json();
}

export function MarketHealthPage() {
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);

  const summaryQuery = useQuery<SummaryResponse, Error>({
    queryKey: ["market-health", "summary", filters],
    queryFn: () => fetchSummary(filters),
    placeholderData: (prev) => prev,
  });

  const trendsQuery = useQuery<TrendsData, Error>({
    queryKey: ["market-health", "trends", filters],
    queryFn: () => fetchTrends(filters),
    placeholderData: (prev) => prev,
  });

  // ---------------------------------------------------------------------------
  // Briefing load time
  // ---------------------------------------------------------------------------
  const pageLoadRef = useRef(Date.now());
  const [briefingTimeMs, setBriefingTimeMs] = useState<number | null>(null);
  const briefingTimedRef = useRef(false);

  useEffect(() => {
    if (
      !summaryQuery.isLoading &&
      !trendsQuery.isLoading &&
      !briefingTimedRef.current
    ) {
      setBriefingTimeMs(Date.now() - pageLoadRef.current);
      briefingTimedRef.current = true;
    }
  }, [summaryQuery.isLoading, trendsQuery.isLoading]);

  // ---------------------------------------------------------------------------
  // Chat
  // ---------------------------------------------------------------------------
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    api: "/api/chat",
    streamProtocol: "text",
  });

  // ---------------------------------------------------------------------------
  // Chat response timing + provenance
  // ---------------------------------------------------------------------------
  const [chatProvenances, setChatProvenances] = useState<
    Map<string, ProvenanceData & { timeMs: number }>
  >(new Map());

  const chatSubmittedAtRef = useRef<number | null>(null);
  const pendingProvenanceRef = useRef<ProvenanceData | null>(null);
  const prevIsLoadingRef = useRef(false);
  const prevMessagesRef = useRef<Message[]>([]);

  useEffect(() => {
    if (prevIsLoadingRef.current && !isLoading && messages.length > 0) {
      const last = messages[messages.length - 1];
      if (
        last?.role === "assistant" &&
        chatSubmittedAtRef.current !== null &&
        pendingProvenanceRef.current !== null
      ) {
        const timeMs = Date.now() - chatSubmittedAtRef.current;
        const provenance = { ...pendingProvenanceRef.current, timeMs };
        setChatProvenances((prev) => new Map(prev).set(last.id, provenance));
        chatSubmittedAtRef.current = null;
        pendingProvenanceRef.current = null;
      }
    }
    prevIsLoadingRef.current = isLoading;
    prevMessagesRef.current = messages;
  }, [isLoading, messages]);

  function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    chatSubmittedAtRef.current = Date.now();
    pendingProvenanceRef.current = {
      source: "chat",
      filters: { ...filters },
      signal: summaryQuery.data?.signal ?? null,
      demandCount: trendsQuery.data?.demand.length ?? 0,
      compCount: trendsQuery.data?.compensation.length ?? 0,
      layoffCount: trendsQuery.data?.layoffs.length ?? 0,
    };
    handleSubmit(e, {
      body: {
        context: {
          role: filters.role,
          seniority: filters.seniority,
          location: filters.location,
        },
      },
    });
  }

  // ---------------------------------------------------------------------------
  // Briefing provenance (always reflects current state)
  // ---------------------------------------------------------------------------
  const briefingProvenance: ProvenanceData = {
    source: "briefing",
    filters,
    signal: summaryQuery.data?.signal ?? null,
    demandCount: trendsQuery.data?.demand.length ?? 0,
    compCount: trendsQuery.data?.compensation.length ?? 0,
    layoffCount: trendsQuery.data?.layoffs.length ?? 0,
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <TopBar />
      <ConversationThread
        messages={messages}
        isLoading={isLoading}
        briefingProvenance={briefingProvenance}
        briefingTimeMs={briefingTimeMs}
        chatProvenances={chatProvenances}
      >
        <MarketBriefingMessage
          filters={filters}
          onFiltersChange={setFilters}
          signal={summaryQuery.data?.signal ?? null}
          implication={summaryQuery.data?.implication ?? null}
          signalLoading={summaryQuery.isLoading}
          signalFetching={summaryQuery.isFetching}
          signalError={summaryQuery.error}
          onRetrySignal={() => summaryQuery.refetch()}
          trends={trendsQuery.data}
          trendsLoading={trendsQuery.isLoading}
          trendsFetching={trendsQuery.isFetching}
          trendsError={trendsQuery.error}
          onRetryTrends={() => trendsQuery.refetch()}
        />
      </ConversationThread>
      <ChatInput
        input={input}
        onChange={handleInputChange}
        onSubmit={onSubmit}
        isLoading={isLoading}
      />
    </div>
  );
}
