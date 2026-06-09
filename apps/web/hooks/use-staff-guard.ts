"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useStaffStore } from "@/stores/staff-store";

/**
 * Guard for staff/manager/admin pages: redirect to /login once we know there's
 * no session (after sessionStorage rehydration). Returns `ready` (safe to render)
 * and the profile.
 */
export function useStaffGuard() {
  const router = useRouter();
  const hasHydrated = useStaffStore((s) => s.hasHydrated);
  const profile = useStaffStore((s) => s.profile);
  const isAuthenticated = useStaffStore((s) => s.isAuthenticated);

  useEffect(() => {
    if (hasHydrated && !isAuthenticated()) router.replace("/login");
  }, [hasHydrated, isAuthenticated, router]);

  return { ready: hasHydrated && Boolean(profile), profile };
}
