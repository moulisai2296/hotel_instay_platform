"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { BottomNav } from "@/components/guest/bottom-nav";
import { useGuestStore } from "@/stores/guest-store";

/**
 * Authed guest-app shell: route guard + bottom nav. Wraps the in-app screens
 * (home/chat/requests/guide/offers/checkout) but NOT the PIN screen at
 * /h/[slug], which lives outside this (app) group.
 */
export default function GuestAppLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { slug: string };
}) {
  const router = useRouter();
  const hasHydrated = useGuestStore((s) => s.hasHydrated);
  const isAuthenticated = useGuestStore((s) => s.isAuthenticated);

  useEffect(() => {
    if (hasHydrated && !isAuthenticated()) {
      router.replace(`/h/${params.slug}`);
    }
  }, [hasHydrated, isAuthenticated, params.slug, router]);

  if (!hasHydrated) {
    return (
      <div className="flex flex-1 items-center justify-center text-sm text-muted-foreground">
        Loading your stay…
      </div>
    );
  }

  if (!isAuthenticated()) return null; // redirecting

  return (
    <div className="flex h-dvh flex-1 flex-col">
      {/* min-h-0 lets a child (e.g. chat) own its internal scroll area */}
      <div className="flex min-h-0 flex-1 flex-col">{children}</div>
      <BottomNav slug={params.slug} />
    </div>
  );
}
