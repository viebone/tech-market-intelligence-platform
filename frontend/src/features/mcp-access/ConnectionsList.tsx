import { useQuery } from "@tanstack/react-query";
import { ConnectedAssistantCard, Connection } from "./ConnectedAssistantCard";
import { EmptyState } from "./EmptyState";

interface ConnectionsResponse {
  connections: Connection[];
  plan: "free" | "premium";
}

async function fetchConnections(): Promise<ConnectionsResponse> {
  const res = await fetch("/api/account/connections", { credentials: "include" });
  if (!res.ok) throw new Error(`Failed to load connections (${res.status})`);
  return res.json();
}

export function ConnectionsList() {
  const query = useQuery<ConnectionsResponse, Error>({
    queryKey: ["account", "connections"],
    queryFn: fetchConnections,
  });

  if (query.isLoading) {
    return (
      <div className="space-y-2">
        <div className="h-16 rounded-lg bg-gray-700 animate-pulse" />
        <div className="h-16 rounded-lg bg-gray-700 animate-pulse" />
      </div>
    );
  }

  if (query.error) {
    return <p className="text-xs text-red-400">Couldn't load your connections. Try again shortly.</p>;
  }

  const { connections, plan } = query.data!;

  if (connections.length === 0) {
    return <EmptyState />;
  }

  return (
    <div className="space-y-3">
      {connections.map((connection) => (
        <ConnectedAssistantCard key={connection.id} connection={connection} plan={plan} />
      ))}
    </div>
  );
}
