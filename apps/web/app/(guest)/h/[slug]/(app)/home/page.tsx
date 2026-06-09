"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  LogOut,
  MessageCircle,
  ListChecks,
  Compass,
  Tag,
  ChevronRight,
  Sparkles,
} from "lucide-react";
import { Aurora } from "@/components/brand/aurora";
import { Wordmark } from "@/components/brand/wordmark";
import { useGuestStore } from "@/stores/guest-store";
import { cn } from "@/lib/utils";

function greeting(d = new Date()) {
  const h = d.getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

const tiles = [
  {
    seg: "chat",
    title: "Request something",
    sub: "Chat or voice with the concierge",
    Icon: MessageCircle,
    span: true,
  },
  { seg: "requests", title: "My requests", sub: "Track status", Icon: ListChecks, span: false },
  { seg: "offers", title: "Offers", sub: "Exclusive deals", Icon: Tag, span: false },
  { seg: "guide", title: "Hotel guide", sub: "Amenities & info", Icon: Compass, span: false },
] as const;

export default function GuestHomePage({
  params,
}: {
  params: { slug: string };
}) {
  const router = useRouter();
  const guest = useGuestStore((s) => s.guest);
  const logout = useGuestStore((s) => s.logout);

  if (!guest) return null;
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
        className="relative z-10 flex flex-1 flex-col gap-5 px-5 pb-6 pt-2"
      >
        <div>
          <p className="text-sm text-muted-foreground">{greeting()}</p>
          <h1 className="font-display text-[26px] font-bold leading-tight text-cream">
            Welcome, <span className="text-gold">{firstName}</span>
          </h1>
        </div>

        <Link
          href={`/h/${params.slug}/checkout`}
          className="flex items-center justify-between rounded-2xl border border-gold/20 bg-gold/[0.07] px-4 py-3 transition-colors hover:border-gold/40"
        >
          <div className="text-sm">
            <p className="font-semibold text-cream">Enjoy your stay</p>
            <p className="text-xs text-muted-foreground">
              Checkout {new Date(guest.checkout_date).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })}
            </p>
          </div>
          <Sparkles className="h-5 w-5 text-gold" />
        </Link>

        <div className="grid grid-cols-2 gap-3">
          {tiles.map(({ seg, title, sub, Icon, span }) => (
            <Link
              key={seg}
              href={`/h/${params.slug}/${seg}`}
              className={cn(
                "group flex flex-col gap-2 rounded-2xl border border-white/10 bg-white/[0.05] p-4 backdrop-blur transition-all hover:border-gold/40 hover:bg-gold/[0.07]",
                span && "col-span-2",
              )}
            >
              <Icon className="h-6 w-6 text-gold" />
              <div className="flex items-end justify-between">
                <div>
                  <p className="text-sm font-semibold text-cream">{title}</p>
                  <p className="text-[11px] text-muted-foreground">{sub}</p>
                </div>
                <ChevronRight className="h-4 w-4 text-cream/25 transition-transform group-hover:translate-x-0.5 group-hover:text-gold" />
              </div>
            </Link>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
