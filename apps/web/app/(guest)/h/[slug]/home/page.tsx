"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { LogOut, MessageCircle, ListChecks, Compass, Tag } from "lucide-react";
import { Aurora } from "@/components/brand/aurora";
import { Wordmark } from "@/components/brand/wordmark";
import { useGuestStore } from "@/stores/guest-store";

const tiles = [
  { Icon: MessageCircle, title: "Request something", sub: "Chat or voice" },
  { Icon: ListChecks, title: "My requests", sub: "Track status" },
  { Icon: Compass, title: "Hotel guide", sub: "Amenities & info" },
  { Icon: Tag, title: "Offers for you", sub: "Exclusive deals" },
] as const;

export default function GuestHomePage({
  params,
}: {
  params: { slug: string };
}) {
  const router = useRouter();
  const hasHydrated = useGuestStore((s) => s.hasHydrated);
  const guest = useGuestStore((s) => s.guest);
  const isAuthenticated = useGuestStore((s) => s.isAuthenticated);
  const logout = useGuestStore((s) => s.logout);

  // Route guard — wait for sessionStorage rehydration before deciding.
  useEffect(() => {
    if (hasHydrated && !isAuthenticated()) {
      router.replace(`/h/${params.slug}`);
    }
  }, [hasHydrated, isAuthenticated, params.slug, router]);

  if (!hasHydrated || !guest) {
    return (
      <div className="flex flex-1 items-center justify-center text-sm text-muted-foreground">
        Loading your stay…
      </div>
    );
  }

  const firstName = guest.guest_name.split(" ")[0];

  return (
    <div className="relative flex flex-1 flex-col overflow-hidden">
      <Aurora />

      <header className="relative z-10 flex items-center justify-between px-5 py-4">
        <Wordmark className="text-lg" />
        <div className="flex items-center gap-2">
          <span className="rounded-full border border-gold/30 bg-gold/15 px-3 py-1 text-xs font-bold text-gold">
            Room {guest.room_number}
          </span>
          <button
            onClick={() => {
              logout();
              router.replace(`/h/${params.slug}`);
            }}
            className="flex h-8 w-8 items-center justify-center rounded-full bg-white/[0.08] text-cream/50 transition-colors hover:text-cream"
            aria-label="Sign out"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </header>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="relative z-10 flex flex-1 flex-col gap-5 px-5 py-2"
      >
        <div>
          <h1 className="font-display text-2xl font-bold text-cream">
            Welcome, <span className="text-gold">{firstName}</span>
          </h1>
          <p className="text-sm text-muted-foreground">
            Checkout {new Date(guest.checkout_date).toLocaleDateString()}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {tiles.map(({ Icon, title, sub }) => (
            <div
              key={title}
              className="flex cursor-not-allowed flex-col gap-2 rounded-2xl border border-white/10 bg-white/[0.05] p-4 opacity-80"
            >
              <Icon className="h-6 w-6 text-gold" />
              <div>
                <p className="text-sm font-semibold text-cream">{title}</p>
                <p className="text-[11px] text-muted-foreground">{sub}</p>
              </div>
            </div>
          ))}
        </div>

        <p className="mt-auto rounded-xl border border-gold/20 bg-gold/[0.06] px-4 py-3 text-center text-xs text-cream/60">
          You&apos;re signed in. The full guest experience — concierge chat,
          voice, request tracking — arrives in the next release.
        </p>
      </motion.div>
    </div>
  );
}
