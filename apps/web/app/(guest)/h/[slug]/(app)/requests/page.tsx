"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { MessageCirclePlus, Loader2 } from "lucide-react";
import { useGuestStore } from "@/stores/guest-store";
import { getGuestSupabase } from "@/lib/guest-supabase";
import { cn } from "@/lib/utils";
import type { RequestPriority, RequestStatus } from "@/types/api";

interface RequestRow {
  id: string;
  ai_title: string | null;
  raw_input: string;
  status: RequestStatus;
  priority: RequestPriority;
  created_at: string;
  ai_items: { item: string; qty: number }[] | null;
}

const STATUS_META: Record<
  RequestStatus,
  { label: string; tone: string; step: number }
> = {
  pending: { label: "Pending", tone: "bg-amber-500/15 text-amber-300", step: 0 },
  assigned: { label: "Assigned", tone: "bg-amber-500/15 text-amber-300", step: 0 },
  in_progress: { label: "In progress", tone: "bg-sky-500/15 text-sky-300", step: 1 },
  completed: { label: "Completed", tone: "bg-emerald-500/15 text-emerald-300", step: 2 },
  escalated: { label: "Escalated", tone: "bg-red-500/15 text-red-300", step: 1 },
  cancelled: { label: "Cancelled", tone: "bg-white/10 text-cream/50", step: -1 },
};

type Filter = "all" | "active" | "completed";
const ACTIVE_STATUSES: RequestStatus[] = ["pending", "assigned", "in_progress", "escalated"];

function timeAgo(iso: string) {
  const mins = Math.round((Date.now() - Date.parse(iso)) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const h = Math.round(mins / 60);
  if (h < 24) return `${h} hr ago`;
  return new Date(iso).toLocaleDateString();
}

export default function RequestsPage({ params }: { params: { slug: string } }) {
  const sessionId = useGuestStore((s) => s.guest?.session_id);
  const [rows, setRows] = useState<RequestRow[] | null>(null);
  const [filter, setFilter] = useState<Filter>("all");

  useEffect(() => {
    if (!sessionId) return;
    const supabase = getGuestSupabase();
    let active = true;

    const load = async () => {
      const { data } = await supabase
        .from("requests")
        .select("id, ai_title, raw_input, status, priority, created_at, ai_items")
        .order("created_at", { ascending: false });
      if (active) setRows((data ?? []) as RequestRow[]);
    };
    load();

    // Live updates: any change to this guest's requests refetches the list.
    const channel = supabase
      .channel("guest-requests")
      .on(
        "postgres_changes",
        {
          event: "*",
          schema: "public",
          table: "requests",
          filter: `guest_session_id=eq.${sessionId}`,
        },
        load,
      )
      .subscribe();

    return () => {
      active = false;
      supabase.removeChannel(channel);
    };
  }, [sessionId]);

  const filtered = useMemo(() => {
    if (!rows) return null;
    if (filter === "active") return rows.filter((r) => ACTIVE_STATUSES.includes(r.status));
    if (filter === "completed") return rows.filter((r) => r.status === "completed");
    return rows;
  }, [rows, filter]);

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <header className="flex items-center justify-between px-5 pb-2 pt-5">
        <h1 className="font-display text-xl font-bold text-cream">My requests</h1>
        <Link
          href={`/h/${params.slug}/chat`}
          className="flex items-center gap-1.5 rounded-full bg-gold/15 px-3 py-1.5 text-xs font-semibold text-gold"
        >
          <MessageCirclePlus className="h-4 w-4" /> New
        </Link>
      </header>

      <div className="flex gap-2 px-5 pb-3">
        {(["all", "active", "completed"] as Filter[]).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cn(
              "rounded-full px-3.5 py-1 text-xs font-semibold capitalize transition-colors",
              filter === f
                ? "bg-gold text-navy"
                : "border border-white/15 text-cream/60",
            )}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="flex min-h-0 flex-1 flex-col gap-2.5 overflow-y-auto px-5 pb-5">
        {filtered === null && (
          <div className="m-auto flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading…
          </div>
        )}

        {filtered && filtered.length === 0 && (
          <div className="m-auto max-w-[16rem] text-center">
            <p className="text-sm font-semibold text-cream">No requests yet</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Ask the concierge for anything — towels, room service, a wake-up
              call — and it&apos;ll show up here.
            </p>
            <Link
              href={`/h/${params.slug}/chat`}
              className="mt-4 inline-block rounded-full bg-gold px-4 py-2 text-xs font-semibold text-navy"
            >
              Start a request
            </Link>
          </div>
        )}

        {filtered?.map((r) => (
          <RequestCard key={r.id} row={r} />
        ))}
      </div>
    </div>
  );
}

function RequestCard({ row }: { row: RequestRow }) {
  const meta = STATUS_META[row.status];
  const title =
    row.ai_title ||
    (row.ai_items?.length
      ? row.ai_items.map((i) => `${i.item}${i.qty > 1 ? ` ×${i.qty}` : ""}`).join(", ")
      : row.raw_input);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-white/10 bg-white/[0.05] p-4"
    >
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-semibold text-cream">{title}</p>
        <span className={cn("shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold", meta.tone)}>
          {meta.label}
        </span>
      </div>
      <p className="mt-0.5 text-[11px] text-muted-foreground">{timeAgo(row.created_at)}</p>

      {meta.step >= 0 && (
        <div className="mt-3 flex items-center gap-1.5">
          {["Received", "In progress", "Done"].map((label, i) => (
            <div key={label} className="flex flex-1 items-center gap-1.5">
              <span
                className={cn(
                  "h-2 w-2 rounded-full",
                  i < meta.step
                    ? "bg-emerald-400"
                    : i === meta.step
                      ? "bg-gold"
                      : "bg-white/15",
                )}
              />
              {i < 2 && (
                <span
                  className={cn(
                    "h-px flex-1",
                    i < meta.step ? "bg-emerald-400/60" : "bg-white/15",
                  )}
                />
              )}
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
