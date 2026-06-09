"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Home, MessageCircle, ListChecks, Compass, Tag } from "lucide-react";
import { cn } from "@/lib/utils";

const items = [
  { seg: "home", label: "Home", Icon: Home },
  { seg: "chat", label: "Chat", Icon: MessageCircle },
  { seg: "requests", label: "Requests", Icon: ListChecks },
  { seg: "guide", label: "Guide", Icon: Compass },
  { seg: "offers", label: "Offers", Icon: Tag },
] as const;

export function BottomNav({ slug }: { slug: string }) {
  const pathname = usePathname();

  return (
    <nav className="sticky bottom-0 z-20 flex border-t border-gold/15 bg-navy/95 px-1 pb-[max(0.4rem,env(safe-area-inset-bottom))] pt-2 backdrop-blur">
      {items.map(({ seg, label, Icon }) => {
        const href = `/h/${slug}/${seg}`;
        const active = pathname === href;
        return (
          <Link
            key={seg}
            href={href}
            className="relative flex flex-1 flex-col items-center gap-1 py-1"
          >
            <Icon
              className={cn(
                "h-[22px] w-[22px] transition-colors",
                active ? "text-gold" : "text-cream/40",
              )}
            />
            <span
              className={cn(
                "text-[10px] transition-colors",
                active ? "text-gold" : "text-cream/40",
              )}
            >
              {label}
            </span>
            {active && (
              <motion.span
                layoutId="guest-nav-active"
                className="absolute -top-2 h-1 w-8 rounded-full bg-gold"
                transition={{ type: "spring", stiffness: 500, damping: 32 }}
              />
            )}
          </Link>
        );
      })}
    </nav>
  );
}
