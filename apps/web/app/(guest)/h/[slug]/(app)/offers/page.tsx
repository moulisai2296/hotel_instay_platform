"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Tag, Loader2, Sparkles } from "lucide-react";
import { getGuestSupabase } from "@/lib/guest-supabase";

interface OfferRow {
  id: string;
  title: string;
  description: string | null;
  discount_pct: number | null;
  valid_until: string | null;
}

export default function OffersPage() {
  const [offers, setOffers] = useState<OfferRow[] | null>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      const { data } = await getGuestSupabase()
        .from("offers")
        .select("id, title, description, discount_pct, valid_until, status")
        .eq("status", "active")
        .order("created_at", { ascending: false });
      if (active) setOffers((data ?? []) as OfferRow[]);
    })();
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <header className="px-5 pb-2 pt-5">
        <h1 className="font-display text-xl font-bold text-cream">Offers for you</h1>
        <p className="text-xs text-muted-foreground">Exclusive deals during your stay</p>
      </header>

      <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto px-5 pb-5">
        {offers === null && (
          <div className="m-auto flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading…
          </div>
        )}

        {offers && offers.length === 0 && (
          <div className="m-auto max-w-[16rem] text-center">
            <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-gold/15">
              <Sparkles className="h-7 w-7 text-gold" />
            </div>
            <p className="text-sm font-semibold text-cream">No offers right now</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Check back soon — your hotel adds exclusive deals during your stay.
            </p>
          </div>
        )}

        {offers?.map((o) => (
          <motion.div
            key={o.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.05]"
          >
            <div className="relative flex h-24 items-center justify-center bg-gradient-to-br from-navy-700 to-navy-800">
              <Tag className="h-8 w-8 text-gold/40" />
              {o.discount_pct ? (
                <span className="absolute right-2 top-2 rounded-full bg-gold px-2 py-0.5 text-[10px] font-bold text-navy">
                  {o.discount_pct}% OFF
                </span>
              ) : null}
            </div>
            <div className="p-4">
              <p className="text-sm font-bold text-cream">{o.title}</p>
              {o.description && (
                <p className="mt-0.5 text-[11px] text-muted-foreground">{o.description}</p>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
