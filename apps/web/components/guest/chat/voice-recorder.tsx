"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Mic, X } from "lucide-react";
import { toast } from "sonner";

/**
 * Full-screen voice capture overlay. Starts recording on mount, shows a live
 * timer + waveform, and returns the recorded audio blob on "Send" so the parent
 * can POST it to /ai/transcribe.
 */
export function VoiceRecorder({
  onResult,
  onCancel,
}: {
  onResult: (audio: Blob) => void;
  onCancel: () => void;
}) {
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const [seconds, setSeconds] = useState(0);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    navigator.mediaDevices
      ?.getUserMedia({ audio: true })
      .then((stream) => {
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        const rec = new MediaRecorder(stream);
        rec.ondataavailable = (e) => {
          if (e.data.size > 0) chunksRef.current.push(e.data);
        };
        rec.start();
        recorderRef.current = rec;
        setReady(true);
      })
      .catch(() => {
        toast.error("Microphone access is needed for voice notes.");
        onCancel();
      });

    const timer = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => {
      cancelled = true;
      clearInterval(timer);
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const stop = (deliver: boolean) => {
    const rec = recorderRef.current;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    if (rec && rec.state !== "inactive") {
      rec.onstop = () => {
        if (deliver) onResult(new Blob(chunksRef.current, { type: "audio/webm" }));
      };
      rec.stop();
    } else if (deliver) {
      onResult(new Blob(chunksRef.current, { type: "audio/webm" }));
    }
  };

  const mm = Math.floor(seconds / 60);
  const ss = String(seconds % 60).padStart(2, "0");

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="absolute inset-0 z-50 flex flex-col items-center justify-center gap-6 bg-navy/97 backdrop-blur"
    >
      <div className="relative flex h-28 w-28 items-center justify-center rounded-full border-2 border-gold bg-gold/10">
        <motion.span
          className="absolute inset-0 rounded-full border border-gold/40"
          animate={{ scale: [1, 1.25], opacity: [0.8, 0] }}
          transition={{ duration: 1.5, repeat: Infinity }}
        />
        <Mic className="h-10 w-10 text-gold" />
      </div>

      <div className="text-2xl font-semibold tabular-nums text-gold">
        {mm}:{ss}
      </div>

      <div className="flex h-8 items-center gap-1">
        {Array.from({ length: 9 }).map((_, i) => (
          <motion.span
            key={i}
            className="w-1 rounded-full bg-gold"
            animate={{ height: ready ? [6, 26, 6] : 6 }}
            transition={{
              duration: 1,
              repeat: Infinity,
              delay: i * 0.08,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>

      <p className="text-sm text-cream">
        {ready ? "Listening… speak your request" : "Starting microphone…"}
      </p>

      <div className="flex items-center gap-3">
        <button
          onClick={() => stop(false)}
          className="flex items-center gap-2 rounded-full border border-white/20 bg-white/[0.08] px-5 py-2.5 text-sm font-semibold text-cream"
        >
          <X className="h-4 w-4" /> Cancel
        </button>
        <button
          onClick={() => stop(true)}
          disabled={!ready}
          className="rounded-full bg-gold px-6 py-2.5 text-sm font-semibold text-navy disabled:opacity-50"
        >
          Send request
        </button>
      </div>
    </motion.div>
  );
}
