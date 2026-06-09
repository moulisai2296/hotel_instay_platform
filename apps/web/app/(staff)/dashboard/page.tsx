"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import { Wordmark } from "@/components/brand/wordmark";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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

  return (
    <div className="min-h-dvh bg-stone">
      <header className="flex items-center justify-between bg-navy px-6 py-3">
        <Wordmark className="text-lg" tone="dark" />
        <div className="flex items-center gap-3">
          <Badge className="bg-gold/20 text-gold hover:bg-gold/20">
            {ROLE_LABEL[profile.role] ?? profile.role}
          </Badge>
          <span className="text-sm text-cream/60">
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

      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="text-xl font-bold text-foreground">
          Welcome, {(profile.display_name ?? profile.email).split(" ")[0]}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          You&apos;re signed in as {ROLE_LABEL[profile.role] ?? profile.role}.
          Your role-specific dashboard — kanban, analytics, admin — ships in the
          next releases.
        </p>

        <div className="mt-6 grid gap-3 rounded-2xl border border-border bg-card p-6 text-sm shadow-card">
          <Row label="Role" value={ROLE_LABEL[profile.role] ?? profile.role} />
          <Row label="Email" value={profile.email} />
          <Row label="Hotel ID" value={profile.hotel_id} mono />
          <Row
            label="Department ID"
            value={profile.department_id ?? "—"}
            mono={Boolean(profile.department_id)}
          />
        </div>
      </main>
    </div>
  );
}

function Row({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-border pb-2 last:border-0 last:pb-0">
      <span className="text-muted-foreground">{label}</span>
      <span className={mono ? "font-mono text-xs text-foreground" : "text-foreground"}>
        {value}
      </span>
    </div>
  );
}
