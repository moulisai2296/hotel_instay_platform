"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import { Wordmark } from "@/components/brand/wordmark";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useStaffStore } from "@/stores/staff-store";
import { cn } from "@/lib/utils";

const ROLE_LABEL: Record<string, string> = {
  staff: "Staff",
  dept_manager: "Department Manager",
  hotel_manager: "Hotel Manager",
  admin: "Admin",
};

/** Shared top bar for the staff/manager/admin surfaces. `nav` is role-dependent. */
export function TopBar({ nav = [] }: { nav?: { label: string; href: string }[] }) {
  const router = useRouter();
  const pathname = usePathname();
  const profile = useStaffStore((s) => s.profile);
  const logout = useStaffStore((s) => s.logout);
  if (!profile) return null;

  return (
    <header className="flex items-center justify-between gap-4 bg-navy px-5 py-3 md:px-6">
      <div className="flex items-center gap-5">
        <Wordmark className="text-lg" tone="dark" />
        {nav.length > 0 && (
          <nav className="hidden items-center gap-1 sm:flex">
            {nav.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
                    active
                      ? "bg-white/10 text-gold"
                      : "text-cream/60 hover:text-cream",
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        )}
      </div>

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
          <span className="hidden sm:inline">Sign out</span>
        </Button>
      </div>
    </header>
  );
}

export { ROLE_LABEL };
