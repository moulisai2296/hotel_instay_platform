"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Building2, ChevronRight, UserRound } from "lucide-react";
import { Wordmark } from "@/components/brand/wordmark";
import { Aurora } from "@/components/brand/aurora";

const roles = [
  {
    href: "/stay",
    title: "I'm a guest",
    desc: "Make requests, explore the hotel, track your stay",
    Icon: UserRound,
    accent: true,
  },
  {
    href: "/login",
    title: "Hotel staff & management",
    desc: "Staff dashboard, manager view, admin panel",
    Icon: Building2,
    accent: false,
  },
] as const;

export default function LandingPage() {
  return (
    <main className="dark relative flex min-h-dvh flex-col items-center justify-center overflow-hidden bg-background px-6 py-12 text-foreground">
      <Aurora />

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="relative z-10 flex w-full max-w-sm flex-col items-center gap-10 text-center"
      >
        <div className="space-y-2">
          <Wordmark className="text-4xl" />
          <p className="text-sm text-muted-foreground">
            In-stay guest experience, elevated.
          </p>
        </div>

        <div className="flex w-full flex-col gap-3.5">
          {roles.map(({ href, title, desc, Icon, accent }, i) => (
            <motion.div
              key={href}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 + i * 0.08, duration: 0.4 }}
            >
              <Link
                href={href}
                className="group flex items-center gap-4 rounded-2xl border border-white/10 bg-white/[0.05] p-5 text-left backdrop-blur transition-all hover:border-gold/50 hover:bg-gold/[0.08]"
              >
                <span
                  className={
                    accent
                      ? "flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-gold/30 bg-gold/15 text-gold"
                      : "flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-white/15 bg-white/[0.07] text-cream/80"
                  }
                >
                  <Icon className="h-6 w-6" />
                </span>
                <span className="flex-1">
                  <span className="block text-[15px] font-bold text-cream">
                    {title}
                  </span>
                  <span className="mt-0.5 block text-xs leading-snug text-muted-foreground">
                    {desc}
                  </span>
                </span>
                <ChevronRight className="h-5 w-5 text-cream/25 transition-transform group-hover:translate-x-0.5 group-hover:text-gold" />
              </Link>
            </motion.div>
          ))}
        </div>

        <p className="text-xs text-cream/30">
          Powered by InStayOS · Your stay, your way
        </p>
      </motion.div>
    </main>
  );
}
