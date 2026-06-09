"use client";

import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, X, Clock, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { useStaffStore } from "@/stores/staff-store";
import { getStaffSupabase } from "@/lib/staff-supabase";
import { api, ApiError } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import type { RequestPriority, RequestStatus } from "@/types/api";

interface Row {
  id: string;
  ai_title: string | null;
  raw_input: string;
  status: RequestStatus;
  priority: RequestPriority;
  created_at: string;
  ai_items: { item: string; qty: number }[] | null;
}

const COLUMNS: { key: string; label: string; statuses: RequestStatus[] }[] = [
  { key: "new", label: "New", statuses: ["pending", "assigned"] },
  { key: "active", label: "In progress", statuses: ["in_progress", "escalated"] },
  { key: "done", label: "Completed", statuses: ["completed"] },
];

const PRIORITY_DOT: Record<RequestPriority, string> = {
  urgent: "bg-red-500",
  high: "bg-red-500",
  medium: "bg-amber-500",
  low: "bg-emerald-500",
};

const STATUS_BADGE: Record<RequestStatus, string> = {
  pending: "bg-amber-100 text-amber-700",
  assigned: "bg-amber-100 text-amber-700",
  in_progress: "bg-sky-100 text-sky-700",
  escalated: "bg-red-100 text-red-700",
  completed: "bg-emerald-100 text-emerald-700",
  cancelled: "bg-stone-200 text-stone-500",
};

function timeAgo(iso: string) {
  const mins = Math.round((Date.now() - Date.parse(iso)) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const h = Math.round(mins / 60);
  if (h < 24) return `${h}h ago`;
  return new Date(iso).toLocaleDateString();
}

const titleOf = (r: Row) =>
  r.ai_title ||
  (r.ai_items?.length
    ? r.ai_items.map((i) => `${i.item}${i.qty > 1 ? ` ×${i.qty}` : ""}`).join(", ")
    : r.raw_input);

export function KanbanBoard() {
  const token = useStaffStore((s) => s.token);
  const hotelId = useStaffStore((s) => s.profile?.hotel_id);
  const [rows, setRows] = useState<Row[] | null>(null);
  const [selected, setSelected] = useState<Row | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!hotelId) return;
    const supabase = getStaffSupabase();
    let active = true;

    const load = async () => {
      const { data } = await supabase
        .from("requests")
        .select("id, ai_title, raw_input, status, priority, created_at, ai_items")
        .order("created_at", { ascending: false });
      if (active) setRows((data ?? []) as Row[]);
    };
    load();

    const channel = supabase
      .channel("staff-requests")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "requests", filter: `hotel_id=eq.${hotelId}` },
        load,
      )
      .subscribe();

    return () => {
      active = false;
      supabase.removeChannel(channel);
    };
  }, [hotelId]);

  const byColumn = useMemo(() => {
    const map: Record<string, Row[]> = { new: [], active: [], done: [] };
    for (const r of rows ?? []) {
      const col = COLUMNS.find((c) => c.statuses.includes(r.status));
      if (col) map[col.key].push(r);
    }
    return map;
  }, [rows]);

  async function move(row: Row, status: RequestStatus, note?: string) {
    if (!token || busy) return;
    setBusy(true);
    try {
      await api.staff.updateRequestStatus(token, row.id, status, note);
      // Optimistic; realtime will also refresh.
      setRows((rs) => rs?.map((r) => (r.id === row.id ? { ...r, status } : r)) ?? null);
      setSelected((s) => (s && s.id === row.id ? { ...s, status } : s));
      toast.success(`Marked ${status.replace("_", " ")}`);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Couldn't update the request.");
    } finally {
      setBusy(false);
    }
  }

  if (rows === null) {
    return (
      <div className="flex flex-1 items-center justify-center text-sm text-muted-foreground">
        <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Loading the board…
      </div>
    );
  }

  return (
    <>
      <div className="grid flex-1 gap-4 md:grid-cols-3">
        {COLUMNS.map((col) => (
          <div key={col.key} className="flex flex-col rounded-2xl bg-stone-surface/60 p-3">
            <div className="mb-2 flex items-center justify-between px-1">
              <h2 className="text-sm font-bold text-foreground">{col.label}</h2>
              <span className="rounded-full bg-card px-2 py-0.5 text-xs font-semibold text-muted-foreground">
                {byColumn[col.key].length}
              </span>
            </div>
            <div className="flex flex-col gap-2.5">
              {byColumn[col.key].length === 0 && (
                <p className="px-1 py-6 text-center text-xs text-muted-foreground">Nothing here</p>
              )}
              {byColumn[col.key].map((r) => (
                <motion.button
                  layout
                  key={r.id}
                  onClick={() => setSelected(r)}
                  className="rounded-xl border border-border bg-card p-3 text-left shadow-sm transition-colors hover:border-gold"
                >
                  <div className="flex items-start gap-2">
                    <span className={cn("mt-1.5 h-2 w-2 shrink-0 rounded-full", PRIORITY_DOT[r.priority])} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-semibold text-foreground">{titleOf(r)}</p>
                      <div className="mt-1 flex items-center gap-2">
                        <span className={cn("rounded-full px-1.5 py-0.5 text-[10px] font-bold", STATUS_BADGE[r.status])}>
                          {r.status.replace("_", " ")}
                        </span>
                        <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
                          <Clock className="h-3 w-3" /> {timeAgo(r.created_at)}
                        </span>
                      </div>
                    </div>
                  </div>
                </motion.button>
              ))}
            </div>
          </div>
        ))}
      </div>

      <AnimatePresence>
        {selected && (
          <DetailPanel
            row={selected}
            busy={busy}
            onClose={() => setSelected(null)}
            onMove={move}
          />
        )}
      </AnimatePresence>
    </>
  );
}

function DetailPanel({
  row,
  busy,
  onClose,
  onMove,
}: {
  row: Row;
  busy: boolean;
  onClose: () => void;
  onMove: (row: Row, status: RequestStatus, note?: string) => void;
}) {
  return (
    <>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 z-40 bg-navy/30 backdrop-blur-sm"
      />
      <motion.aside
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ type: "spring", stiffness: 380, damping: 38 }}
        className="fixed right-0 top-0 z-50 flex h-dvh w-full max-w-md flex-col bg-card shadow-2xl"
      >
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <h3 className="font-bold text-foreground">Request detail</h3>
          <button onClick={onClose} aria-label="Close" className="text-muted-foreground hover:text-foreground">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto px-5 py-5">
          <div>
            <p className="text-lg font-bold text-foreground">{titleOf(row)}</p>
            <span className={cn("mt-1 inline-block rounded-full px-2 py-0.5 text-[11px] font-bold", STATUS_BADGE[row.status])}>
              {row.status.replace("_", " ")}
            </span>
          </div>
          <Field label="Guest's words" value={row.raw_input} />
          <Field label="Priority" value={row.priority} />
          <Field label="Created" value={new Date(row.created_at).toLocaleString()} />
        </div>

        <div className="space-y-2 border-t border-border p-5">
          {(row.status === "pending" || row.status === "assigned") && (
            <Button disabled={busy} onClick={() => onMove(row, "in_progress")} className="w-full bg-navy text-cream hover:bg-navy-800">
              Start working
            </Button>
          )}
          {(row.status === "in_progress" || row.status === "escalated") && (
            <Button disabled={busy} onClick={() => onMove(row, "completed")} className="w-full bg-emerald-600 text-white hover:bg-emerald-700">
              Mark completed
            </Button>
          )}
          {row.status === "in_progress" && (
            <Button
              disabled={busy}
              variant="outline"
              onClick={() => onMove(row, "escalated")}
              className="w-full border-red-200 text-red-600 hover:bg-red-50"
            >
              <AlertTriangle className="mr-1.5 h-4 w-4" /> Escalate
            </Button>
          )}
          {row.status === "completed" && (
            <p className="text-center text-sm text-muted-foreground">This request is complete.</p>
          )}
        </div>
      </motion.aside>
    </>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-0.5 text-sm capitalize text-foreground">{value}</p>
    </div>
  );
}
