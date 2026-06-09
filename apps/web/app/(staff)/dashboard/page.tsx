"use client";

import { TopBar, navForRole } from "@/components/staff/top-bar";
import { KanbanBoard } from "@/components/staff/kanban-board";
import { useStaffGuard } from "@/hooks/use-staff-guard";

export default function DashboardPage() {
  const { ready, profile } = useStaffGuard();

  if (!ready || !profile) {
    return (
      <div className="flex min-h-dvh items-center justify-center text-sm text-muted-foreground">
        Loading…
      </div>
    );
  }

  const isDeptScoped = profile.role === "staff" || profile.role === "dept_manager";

  return (
    <div className="flex min-h-dvh flex-col bg-stone">
      <TopBar nav={navForRole(profile.role)} />
      <main className="flex flex-1 flex-col gap-4 p-5 md:p-6">
        <div>
          <h1 className="text-xl font-bold text-foreground">Request queue</h1>
          <p className="text-sm text-muted-foreground">
            {isDeptScoped
              ? "Live requests for your department"
              : "Live requests across your hotel"}{" "}
            · updates in real time
          </p>
        </div>
        <KanbanBoard />
      </main>
    </div>
  );
}
