import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { scopeLabel } from "./scopeLabels";

export interface Connection {
  id: string;
  client_name: string;
  scopes: string[];
  created_at: string;
  revoked_at: string | null;
}

function relativeTime(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (days <= 0) return "today";
  if (days === 1) return "1 day ago";
  return `${days} days ago`;
}

async function revokeConnection(id: string): Promise<void> {
  const res = await fetch(`/api/account/connections/${id}`, {
    method: "DELETE",
    credentials: "include",
  });
  if (!res.ok && res.status !== 404) {
    throw new Error(`Failed to revoke connection (${res.status})`);
  }
}

/**
 * One Connected Assistant, sized for the Output Panel's fixed 320px width —
 * design/visual-design.md's "Output Panel — Settings tab" component
 * aesthetics: vertically stacked, never side-by-side.
 */
interface ConnectedAssistantCardProps {
  connection: Connection;
  /** The signed-in user's plan — a property of the user, not the
   * connection (backend/specs/mcp-access/api.md's Data Models note), so
   * it's passed down once from ConnectionsList's own fetch rather than
   * each card re-deriving it. */
  plan: "free" | "premium";
}

export function ConnectedAssistantCard({ connection, plan }: ConnectedAssistantCardProps) {
  const [confirming, setConfirming] = useState(false);
  const queryClient = useQueryClient();

  const revokeMutation = useMutation({
    mutationFn: () => revokeConnection(connection.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["account", "connections"] });
    },
  });

  return (
    <div className="rounded-lg border border-gray-700 bg-gray-800 p-3 space-y-2">
      <div>
        <p className="text-sm font-medium text-gray-100">{connection.client_name}</p>
        <p className="text-[11px] text-gray-400">Connected {relativeTime(connection.created_at)}</p>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {connection.scopes.map((scope) => (
          <span
            key={scope}
            className="rounded-full bg-gray-700 px-2.5 py-1 text-[11px] font-medium text-gray-100"
          >
            {scopeLabel(scope)}
          </span>
        ))}
      </div>

      {/* Plan tier badge — Status badge pattern, Free=amber/neutral, Premium=emerald.
          The tier is the signed-in user's, shown identically on every card, per
          backend/specs/mcp-access/api.md's "no plan_tier column per connection". */}
      <span
        className={
          "inline-block rounded px-2 py-0.5 text-xs font-medium " +
          (plan === "premium" ? "bg-emerald-600/15 text-emerald-400" : "bg-amber-600/15 text-amber-400")
        }
      >
        {plan === "premium" ? "Premium" : "Free"}
      </span>

      <div className="flex justify-end pt-1">
        {confirming ? (
          <div className="flex items-center gap-2 text-xs">
            <span className="text-gray-400">Revoke access?</span>
            <button
              type="button"
              onClick={() => revokeMutation.mutate()}
              disabled={revokeMutation.isPending}
              className="text-red-400 hover:text-red-300"
            >
              Yes
            </button>
            <button type="button" onClick={() => setConfirming(false)} className="text-gray-500 hover:text-gray-300">
              No
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setConfirming(true)}
            className="text-xs text-gray-400 hover:text-gray-200 transition-colors duration-150"
          >
            Revoke
          </button>
        )}
      </div>
    </div>
  );
}
