"use client";

import { motion } from "framer-motion";
import { Mic, Send } from "lucide-react";

/**
 * Floating 3D phone showing the guest concierge — the hero product visual.
 * Perspective-tilted and gently floating (CSS 3D + Framer, no WebGL).
 */
export function PhoneMockup() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30, rotateY: -18 }}
      animate={{ opacity: 1, y: 0, rotateY: -14 }}
      transition={{ duration: 0.9, ease: "easeOut" }}
      style={{ transformPerspective: 1200 }}
      className="relative [transform-style:preserve-3d]"
    >
      <motion.div
        animate={{ y: [0, -14, 0] }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
        style={{ rotateX: 6, rotateY: -10 }}
        className="relative mx-auto w-[260px] rounded-[2.2rem] border-2 border-gold/30 bg-navy-900 p-3 shadow-[0_40px_80px_-20px_rgba(201,168,76,0.35)]"
      >
        {/* notch */}
        <div className="mx-auto mb-2 h-1.5 w-16 rounded-full bg-white/15" />
        <div className="overflow-hidden rounded-[1.6rem] bg-navy-900">
          {/* header */}
          <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
            <span className="font-display text-sm font-bold text-cream">
              <span className="text-gold">Stay</span>OS
            </span>
            <span className="rounded-full border border-gold/30 bg-gold/15 px-2 py-0.5 text-[10px] font-bold text-gold">
              Room 412
            </span>
          </div>
          {/* chat */}
          <div className="space-y-2.5 px-4 py-4">
            <div className="max-w-[80%] rounded-2xl rounded-bl-md border border-white/10 bg-white/[0.07] px-3 py-2 text-[11px] leading-snug text-cream">
              Good evening, Arjun — how can I help?
            </div>
            <div className="ml-auto max-w-[80%] rounded-2xl rounded-br-md bg-gold px-3 py-2 text-[11px] font-medium leading-snug text-navy">
              Can I get 2 extra towels and a late checkout?
            </div>
            <div className="max-w-[85%] rounded-2xl rounded-bl-md border border-white/10 bg-white/[0.07] px-3 py-2 text-[11px] leading-snug text-cream">
              Done! Towels are on the way and late checkout is confirmed for 2 PM. ✨
              <div className="mt-1.5 flex gap-1">
                <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[9px] font-semibold text-emerald-300">
                  Housekeeping
                </span>
                <span className="rounded-full bg-sky-500/20 px-2 py-0.5 text-[9px] font-semibold text-sky-300">
                  Front desk
                </span>
              </div>
            </div>
          </div>
          {/* input */}
          <div className="flex items-center gap-2 border-t border-white/10 px-3 py-3">
            <div className="h-8 flex-1 rounded-full border border-white/15 bg-white/[0.07]" />
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gold">
              <Mic className="h-4 w-4 text-navy" />
            </div>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10">
              <Send className="h-3.5 w-3.5 text-gold" />
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
