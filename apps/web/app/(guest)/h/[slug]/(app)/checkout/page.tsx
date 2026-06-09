"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Star, Luggage, Car, DoorOpen, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useGuestStore } from "@/stores/guest-store";
import { api, ApiError } from "@/lib/api-client";
import { cn } from "@/lib/utils";

export default function CheckoutPage({ params }: { params: { slug: string } }) {
  const router = useRouter();
  const token = useGuestStore((s) => s.token);
  const guest = useGuestStore((s) => s.guest);
  const [rating, setRating] = useState(0);
  const [busy, setBusy] = useState<string | null>(null);

  if (!guest) return null;

  async function raise(key: string, text: string) {
    if (!token || busy) return;
    setBusy(key);
    try {
      await api.requests.create(token, { raw_input: text, input_mode: "chip" });
      toast.success("Request sent to the team");
      router.push(`/h/${params.slug}/requests`);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Couldn't send that request.");
    } finally {
      setBusy(null);
    }
  }

  const actions = [
    { key: "luggage", label: "Request luggage pickup", Icon: Luggage, text: "I'd like luggage pickup for checkout." },
    { key: "taxi", label: "Request a taxi / car", Icon: Car, text: "Please arrange a taxi for my checkout." },
    { key: "checkout", label: "Request late / express checkout", Icon: DoorOpen, text: "I'd like to arrange my checkout." },
  ] as const;

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-y-auto px-5 pb-6 pt-5">
      <h1 className="font-display text-xl font-bold text-cream">Checkout</h1>
      <p className="text-xs text-muted-foreground">Room {guest.room_number}</p>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="mt-4 space-y-2.5 rounded-2xl border border-white/10 bg-white/[0.05] p-4"
      >
        <Row label="Guest" value={guest.guest_name} />
        <Row label="Room" value={guest.room_number} />
        <Row
          label="Checkout"
          value={new Date(guest.checkout_date).toLocaleDateString(undefined, {
            weekday: "short",
            month: "short",
            day: "numeric",
          })}
        />
      </motion.div>

      <div className="mt-4 rounded-2xl border border-white/10 bg-white/[0.05] p-4">
        <p className="text-sm font-semibold text-cream">Rate your stay</p>
        <div className="mt-2 flex gap-2">
          {[1, 2, 3, 4, 5].map((n) => (
            <button key={n} onClick={() => setRating(n)} aria-label={`${n} stars`}>
              <Star
                className={cn(
                  "h-7 w-7 transition-colors",
                  n <= rating ? "fill-gold text-gold" : "text-white/20",
                )}
              />
            </button>
          ))}
        </div>
        {rating > 0 && (
          <p className="mt-2 text-xs text-muted-foreground">
            Thanks for the feedback — we&apos;ll share it with the team.
          </p>
        )}
      </div>

      <div className="mt-4 space-y-2.5">
        {actions.map(({ key, label, Icon, text }) => (
          <button
            key={key}
            onClick={() => raise(key, text)}
            disabled={busy !== null}
            className="flex w-full items-center gap-3 rounded-xl border border-white/12 bg-white/[0.06] px-4 py-3 text-left text-sm font-medium text-cream transition-colors hover:border-gold/40 disabled:opacity-50"
          >
            {busy === key ? (
              <Loader2 className="h-5 w-5 animate-spin text-gold" />
            ) : (
              <Icon className="h-5 w-5 text-gold" />
            )}
            {label}
          </button>
        ))}
      </div>

      <p className="mt-4 text-center text-[11px] text-cream/40">
        Final billing is settled at the front desk.
      </p>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-white/8 pb-2 text-sm last:border-0 last:pb-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium text-cream">{value}</span>
    </div>
  );
}
