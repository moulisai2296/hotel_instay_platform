"use client";

import { motion } from "framer-motion";

/**
 * Soft animated gold aurora for dark (guest) screens — gives the navy depth and
 * a quiet "expensive" shimmer without distracting. Pointer-events: none.
 */
export function Aurora() {
  return (
    <div
      aria-hidden
      className="pointer-events-none absolute inset-0 overflow-hidden"
    >
      <motion.div
        className="absolute -left-24 -top-24 h-72 w-72 rounded-full bg-gold/20 blur-3xl"
        animate={{ x: [0, 30, 0], y: [0, 20, 0], opacity: [0.25, 0.4, 0.25] }}
        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute -right-20 top-1/3 h-64 w-64 rounded-full bg-navy-700/40 blur-3xl"
        animate={{ x: [0, -24, 0], y: [0, 28, 0], opacity: [0.3, 0.5, 0.3] }}
        transition={{ duration: 14, repeat: Infinity, ease: "easeInOut", delay: 1 }}
      />
    </div>
  );
}
