"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import { Wordmark } from "@/components/brand/wordmark";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { KanbanBoard } from "@/components/staff/kanban-board";
import { useStaffStore } from "@/stores/staff-store";

const ROLE_LABEL: Record<string, string> = {
  staff: "Staff",
  dept_manager: "Department Manager",
  hotel_manager: "Hotel Manager",
  admin: "Admin",
};

export default function DashboardPage() {
  const router = useRouter();
  const hasHydrated = useStaffStore((s) => s.hasHydrated);
  const profile = useStaffStore((s) => s.profile);
  const isAuthenticated = useStaffStore((s) => s.isAuthenticated);
  const logout = useStaffStore((s) => s.logout);

  useEffect(() => {
    if (hasHydrated && !isAuthenticated()) router.replace("/login");
  }, [hasHydrated, isAuthenticated, router]);

  if (!hasHydrated || !profile) {
    return (
      <div className="flex min-h-dvh items-center justify-center text-sm text-muted-foreground">
        Loading…
      </div>
    );
  }

  const isDeptScoped = profile.role === "staff" || profile.role === "dept_manager";

  return (
    <div className="flex min-h-dvh flex-col bg-stone">
      <header className="flex items-center justify-between bg-navy px-6 py-3">
        <Wordmark className="text-lg" tone="dark" />
        <div className="flex items-center gap-3">
          <Badge className="bg-gold/20 text-gold hover:bg-gold/20">
            {ROLE_LABEL[profile.role] ?? profile.role}
          </Badge>
          <span className="hidden text-sm text-cream/60 sm:inline">
            {profile.display_name ?? profile.email}
          </span>
          <Button
            size="sm"
            variant="ghost"
            onClick={async () => {
              await logout();
              router.replace("/login");
            }}
            className="text-cream/70 hover:bg-white/10 hover:text-cream"
          >
            <LogOut className="mr-1.5 h-4 w-4" />
            Sign out
          </Button>
        </div>
      </header>

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
