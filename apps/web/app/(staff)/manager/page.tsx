"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Loader2, AlertTriangle, Clock, ListChecks, CheckCircle2, ArrowRight } from "lucide-react";
import Link from "next/link";
import { TopBar, navForRole } from "@/components/staff/top-bar";
import { useStaffGuard } from "@/hooks/use-staff-guard";
import { useStaffStore } from "@/stores/staff-store";
import { getStaffSupabase } from "@/lib/staff-supabase";
import type { DepartmentType, RequestPriority, RequestStatus } from "@/types/api";
import { cn } from "@/lib/utils";

interface ReqRow {
  id: string;
  status: RequestStatus;
  priority: RequestPriority;
  department_id: string;
  ai_title: string | null;
  raw_input: string;
  created_at: string;
  completed_at: string | null;
  resolution_time_mins: number | null;
}
interface DeptRow {
  id: string;
  type: DepartmentType;
  display_name: string | null;
}

const DEPT_LABEL: Record<DepartmentType, string> = {
  housekeeping: "Housekeeping",
  fb: "F&B",
  maintenance: "Maintenance",
  concierge: "Concierge",
  spa: "Spa",
  front_desk: "Front Desk",
};
const ACTIVE: RequestStatus[] = ["pending", "assigned", "in_progress", "escalated"];
const PENDING: RequestStatus[] = ["pending", "assigned"];

export default function ManagerPage() {
  const router = useRouter();
  const { ready, profile } = useStaffGuard();
  const hotelId = useStaffStore((s) => s.profile?.hotel_id);

  const [reqs, setReqs] = useState<ReqRow[] | null>(null);
  const [depts, setDepts] = useState<DeptRow[]>([]);

  // Managers only — staff/dept_manager land on the queue instead.
  const isManager = profile?.role === "hotel_manager" || profile?.role === "admin";
  useEffect(() => {
    if (ready && profile && !isManager) router.replace("/dashboard");
  }, [ready, profile, isManager, router]);

  useEffect(() => {
    if (!hotelId || !isManager) return;
    const supabase = getStaffSupabase();
    let active = true;

    const load = async () => {
      const [{ data: r }, { data: d }] = await Promise.all([
        supabase
          .from("requests")
          .select("id, status, priority, department_id, ai_title, raw_input, created_at, completed_at, resolution_time_mins")
          .order("created_at", { ascending: false }),
        supabase.from("departments").select("id, type, display_name"),
      ]);
      if (!active) return;
      setReqs((r ?? []) as ReqRow[]);
      setDepts((d ?? []) as DeptRow[]);
    };
    load();

    const channel = supabase
      .channel("manager-requests")
      .on("postgres_changes", { event: "*", schema: "public", table: "requests", filter: `hotel_id=eq.${hotelId}` }, load)
      .subscribe();
    return () => {
      active = false;
      supabase.removeChannel(channel);
    };
  }, [hotelId, isManager]);

  const stats = useMemo(() => {
    const rows = reqs ?? [];
    const todayStart = new Date();
    todayStart.setHours(0, 0, 0, 0);
    const completed = rows.filter((r) => r.status === "completed");
    const resolved = completed
      .map((r) => r.resolution_time_mins)
      .filter((m): m is number => typeof m === "number");
    const deptName = (id: string) => {
      const d = depts.find((x) => x.id === id);
      return d ? d.display_name || DEPT_LABEL[d.type] : "Unassigned";
    };
    const deptMap = new Map<string, { name: string; active: number; pending: number }>();
    for (const r of rows) {
      const name = deptName(r.department_id);
      const e = deptMap.get(name) ?? { name, active: 0, pending: 0 };
      if (ACTIVE.includes(r.status)) e.active += 1;
      if (PENDING.includes(r.status)) e.pending += 1;
      deptMap.set(name, e);
    }
    return {
      active: rows.filter((r) => ACTIVE.includes(r.status)).length,
      completedToday: completed.filter((r) => r.completed_at && Date.parse(r.completed_at) >= todayStart.getTime()).length,
      avgResolution: resolved.length ? Math.round(resolved.reduce((a, b) => a + b, 0) / resolved.length) : null,
      escalations: rows.filter((r) => r.status === "escalated").length,
      departments: Array.from(deptMap.values()).sort((a, b) => b.active - a.active),
      alerts: rows.filter((r) => r.status === "escalated").slice(0, 6).map((r) => ({ ...r, deptName: deptName(r.department_id) })),
    };
  }, [reqs, depts]);

  if (!ready || !profile || !isManager) {
    return (
      <div className="flex min-h-dvh items-center justify-center text-sm text-muted-foreground">
        Loading…
      </div>
    );
  }

  const maxActive = Math.max(1, ...stats.departments.map((d) => d.active));

  return (
    <div className="flex min-h-dvh flex-col bg-stone">
      <TopBar nav={navForRole(profile.role)} />
      <main className="mx-auto w-full max-w-5xl flex-1 space-y-5 p-5 md:p-6">
        <div>
          <h1 className="text-xl font-bold text-foreground">Hotel overview</h1>
          <p className="text-sm text-muted-foreground">
            Live operations across all departments
          </p>
        </div>

        {reqs === null ? (
          <div className="flex items-center gap-2 py-10 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading…
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <Kpi label="Active requests" value={stats.active} Icon={ListChecks} tone="amber" />
              <Kpi label="Avg resolution" value={stats.avgResolution !== null ? `${stats.avgResolution}m` : "—"} Icon={Clock} />
              <Kpi label="Completed today" value={stats.completedToday} Icon={CheckCircle2} tone="green" />
              <Kpi label="Escalations" value={stats.escalations} Icon={AlertTriangle} tone={stats.escalations ? "red" : undefined} />
            </div>

            <div className="grid gap-5 lg:grid-cols-2">
              <section className="rounded-2xl border border-border bg-card p-5 shadow-card">
                <h2 className="mb-3 text-sm font-bold text-foreground">Department load</h2>
                {stats.departments.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No requests yet.</p>
                ) : (
                  <div className="space-y-3">
                    {stats.departments.map((d) => (
                      <div key={d.name}>
                        <div className="mb-1 flex items-center justify-between text-sm">
                          <span className="font-medium text-foreground">{d.name}</span>
                          <span className="text-muted-foreground">
                            {d.active} active{d.pending ? ` · ${d.pending} pending` : ""}
                          </span>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-stone-surface">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${(d.active / maxActive) * 100}%` }}
                            className={cn(
                              "h-full rounded-full",
                              d.pending >= 3 ? "bg-amber-500" : "bg-navy",
                            )}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>

              <section className="rounded-2xl border border-border bg-card p-5 shadow-card">
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="text-sm font-bold text-foreground">Alerts</h2>
                  <Link href="/dashboard" className="flex items-center gap-1 text-xs font-semibold text-gold">
                    Open queue <ArrowRight className="h-3 w-3" />
                  </Link>
                </div>
                {stats.alerts.length === 0 ? (
                  <div className="flex flex-col items-center py-6 text-center">
                    <CheckCircle2 className="mb-2 h-7 w-7 text-emerald-500" />
                    <p className="text-sm text-muted-foreground">No escalations — all clear.</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {stats.alerts.map((a) => (
                      <div key={a.id} className="flex items-start gap-2 rounded-xl border border-red-100 bg-red-50/60 p-3">
                        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-500" />
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-foreground">
                            {a.ai_title || a.raw_input}
                          </p>
                          <p className="text-[11px] text-muted-foreground">{a.deptName} · escalated</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

function Kpi({
  label,
  value,
  Icon,
  tone,
}: {
  label: string;
  value: string | number;
  Icon: typeof Clock;
  tone?: "amber" | "green" | "red";
}) {
  const toneCls =
    tone === "amber"
      ? "text-amber-600"
      : tone === "green"
        ? "text-emerald-600"
        : tone === "red"
          ? "text-red-600"
          : "text-foreground";
  return (
    <div className="rounded-2xl border border-border bg-card p-4 shadow-card">
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">{label}</span>
        <Icon className={cn("h-4 w-4", toneCls)} />
      </div>
      <p className={cn("mt-1 text-2xl font-bold", toneCls)}>{value}</p>
    </div>
  );
}
