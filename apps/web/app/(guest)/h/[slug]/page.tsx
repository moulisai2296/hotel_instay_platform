"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import { Aurora } from "@/components/brand/aurora";
import { Wordmark } from "@/components/brand/wordmark";
import { PinPad } from "@/components/guest/pin-pad";
import { Input } from "@/components/ui/input";
import { useGuestStore } from "@/stores/guest-store";
import { ApiError } from "@/lib/api-client";

const PIN_LENGTH = 6;

function prettyHotel(slug: string) {
  return slug
    .split("-")
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export default function GuestPinPage({
  params,
}: {
  params: { slug: string };
}) {
  const { slug } = params;
  const router = useRouter();
  const verifyPin = useGuestStore((s) => s.verifyPin);

  const [room, setRoom] = useState("");
  const [pin, setPin] = useState("");
  const [error, setError] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Auto-submit once a full PIN is entered (and a room is present).
  useEffect(() => {
    if (pin.length !== PIN_LENGTH || submitting) return;
    if (!room.trim()) {
      toast.error("Enter your room number first");
      setPin("");
      return;
    }
    void attempt(room.trim(), pin);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pin]);

  async function attempt(roomNumber: string, code: string) {
    setSubmitting(true);
    setError(false);
    try {
      await verifyPin({ hotel_slug: slug, room_number: roomNumber, pin: code });
      toast.success("Welcome back!");
      router.replace(`/h/${slug}/home`);
    } catch (err) {
      const message =
        err instanceof ApiError && err.code === "INVALID_CREDENTIALS"
          ? "That room and PIN don't match. Please try again."
          : err instanceof ApiError && err.code === "RATE_LIMITED"
            ? "Too many attempts. Please wait a moment."
            : "Something went wrong. Please try again.";
      setError(true);
      toast.error(message);
      setTimeout(() => {
        setPin("");
        setError(false);
      }, 600);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="relative flex flex-1 flex-col overflow-hidden px-6 py-6">
      <Aurora />

      <Link
        href="/stay"
        className="relative z-10 flex h-9 w-9 items-center justify-center rounded-full border border-white/12 bg-white/[0.06] text-cream/60 transition-colors hover:text-cream"
        aria-label="Back"
      >
        <ArrowLeft className="h-4 w-4" />
      </Link>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="relative z-10 flex flex-1 flex-col items-center justify-center gap-6 text-center"
      >
        <div className="space-y-1.5">
          <Wordmark className="text-2xl" />
          <p className="text-[11px] font-semibold uppercase tracking-[0.15em] text-gold/70">
            {prettyHotel(slug)}
          </p>
        </div>

        <div className="space-y-1">
          <h1 className="font-display text-xl font-bold text-cream">
            Welcome to your stay
          </h1>
          <p className="text-sm text-muted-foreground">
            Enter your room number and 6-digit PIN
          </p>
        </div>

        <div className="w-full max-w-[280px]">
          <Input
            inputMode="numeric"
            value={room}
            onChange={(e) => setRoom(e.target.value.replace(/[^0-9a-zA-Z]/g, ""))}
            placeholder="Room number"
            disabled={submitting}
            className="h-12 border-white/15 bg-white/[0.07] text-center text-base text-cream placeholder:text-cream/30 focus-visible:ring-gold"
          />
        </div>

        <PinPad
          value={pin}
          onChange={setPin}
          length={PIN_LENGTH}
          error={error}
          disabled={submitting}
        />

        <p className="text-xs text-cream/30">
          Your PIN is on your check-in confirmation
        </p>
      </motion.div>
    </div>
  );
}
