"use client";

import { Delete } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

const KEYS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "", "0", "del"];

interface PinPadProps {
  value: string;
  onChange: (next: string) => void;
  length?: number;
  /** Triggers the shake animation + red dots when true. */
  error?: boolean;
  disabled?: boolean;
}

export function PinPad({
  value,
  onChange,
  length = 6,
  error = false,
  disabled = false,
}: PinPadProps) {
  const press = (k: string) => {
    if (disabled) return;
    if (k === "del") {
      onChange(value.slice(0, -1));
      return;
    }
    if (k === "" || value.length >= length) return;
    onChange((value + k).slice(0, length));
  };

  return (
    <div className="flex w-full flex-col items-center gap-7">
      <motion.div
        className="flex gap-3.5"
        animate={error ? { x: [0, -8, 8, -6, 6, 0] } : { x: 0 }}
        transition={{ duration: 0.4 }}
      >
        {Array.from({ length }).map((_, i) => {
          const filled = i < value.length;
          return (
            <motion.span
              key={i}
              initial={false}
              animate={{ scale: filled ? 1 : 0.85 }}
              transition={{ type: "spring", stiffness: 500, damping: 28 }}
              className={cn(
                "h-3.5 w-3.5 rounded-full border-2 transition-colors",
                error
                  ? "border-destructive bg-destructive/70"
                  : filled
                    ? "border-gold bg-gold"
                    : "border-gold/40 bg-transparent",
              )}
            />
          );
        })}
      </motion.div>

      <div className="grid w-full max-w-[280px] grid-cols-3 gap-3">
        {KEYS.map((k, i) =>
          k === "" ? (
            <span key={i} />
          ) : (
            <motion.button
              key={i}
              type="button"
              whileTap={{ scale: 0.94 }}
              disabled={disabled}
              onClick={() => press(k)}
              className={cn(
                "flex h-14 items-center justify-center rounded-xl border border-white/10 bg-white/[0.06] text-xl font-medium text-cream transition-colors",
                "hover:border-gold/50 hover:bg-gold/10 active:bg-gold/20 disabled:opacity-40",
                k === "del" && "text-muted-foreground",
              )}
              aria-label={k === "del" ? "Delete" : `Digit ${k}`}
            >
              {k === "del" ? <Delete className="h-5 w-5" /> : k}
            </motion.button>
          ),
        )}
      </div>
    </div>
  );
}
