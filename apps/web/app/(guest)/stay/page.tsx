"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeft, ArrowRight, QrCode } from "lucide-react";
import { Wordmark } from "@/components/brand/wordmark";
import { Aurora } from "@/components/brand/aurora";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

/** Slugify a hotel code/name typed by a guest who reached the bare domain. */
function toSlug(input: string) {
  return input
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}

export default function StayEntryPage() {
  const router = useRouter();
  const [code, setCode] = useState("");
  const slug = toSlug(code);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (slug) router.push(`/h/${slug}`);
  };

  return (
    <div className="relative flex flex-1 flex-col overflow-hidden px-6 py-6">
      <Aurora />

      <Link
        href="/"
        className="relative z-10 flex h-9 w-9 items-center justify-center rounded-full border border-white/12 bg-white/[0.06] text-cream/60 transition-colors hover:text-cream"
        aria-label="Back"
      >
        <ArrowLeft className="h-4 w-4" />
      </Link>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="relative z-10 flex flex-1 flex-col items-center justify-center gap-7 text-center"
      >
        <Wordmark className="text-3xl" />

        <div className="space-y-1.5">
          <h1 className="font-display text-xl font-bold text-cream">
            Find your hotel
          </h1>
          <p className="mx-auto max-w-[18rem] text-sm text-muted-foreground">
            Normally you&apos;ll scan the QR code in your room. Otherwise, enter
            your hotel&apos;s code below.
          </p>
        </div>

        <form onSubmit={submit} className="w-full max-w-xs space-y-3">
          <Input
            autoFocus
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="e.g. grand-hotel"
            className="h-12 border-white/15 bg-white/[0.07] text-center text-base text-cream placeholder:text-cream/30 focus-visible:ring-gold"
          />
          <Button
            type="submit"
            disabled={!slug}
            className="h-12 w-full bg-gold text-navy hover:bg-gold-400"
          >
            Continue
            <ArrowRight className="ml-1 h-4 w-4" />
          </Button>
        </form>

        <div className="flex items-center gap-2 text-xs text-cream/30">
          <QrCode className="h-4 w-4" />
          <span>Tip: the room QR takes you straight to the PIN screen</span>
        </div>
      </motion.div>
    </div>
  );
}
