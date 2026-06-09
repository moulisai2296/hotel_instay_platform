"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, Send, CheckCircle2, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { VoiceRecorder } from "@/components/guest/chat/voice-recorder";
import { useGuestStore } from "@/stores/guest-store";
import { api, ApiError } from "@/lib/api-client";
import { getGuestSupabase } from "@/lib/guest-supabase";
import { cn } from "@/lib/utils";
import type { InputMode } from "@/types/api";

type ChatMsg = {
  id: string;
  role: "guest" | "assistant";
  content: string;
  pending?: boolean;
  raised?: boolean; // a service request was created from this turn
};

const CHIPS = [
  "Extra towels please",
  "Room service menu",
  "The AC isn't cooling",
  "Set a wake-up call for 7am",
  "Fresh bed linen",
];

let counter = 0;
const nid = () => `m${Date.now()}_${counter++}`;

export default function ChatPage({ params }: { params: { slug: string } }) {
  const token = useGuestStore((s) => s.token);
  const guest = useGuestStore((s) => s.guest);

  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [showVoice, setShowVoice] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Load prior chat history straight from Supabase (RLS-scoped to this session).
  useEffect(() => {
    let active = true;
    (async () => {
      const { data, error } = await getGuestSupabase()
        .from("guest_interactions")
        .select("role, content, input_mode, created_at")
        .order("created_at");
      if (!active) return;
      if (!error && data) {
        setMessages(
          data.map((r) => ({
            id: nid(),
            role: r.role === "assistant" ? "assistant" : "guest",
            content: r.content as string,
          })),
        );
      }
      setLoaded(true);
    })();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  async function send(text: string, mode: InputMode) {
    const content = text.trim();
    if (!content || !token || sending) return;
    setInput("");
    const typingId = nid();
    setMessages((m) => [
      ...m,
      { id: nid(), role: "guest", content },
      { id: typingId, role: "assistant", content: "", pending: true },
    ]);
    setSending(true);
    try {
      const res = await api.requests.create(token, {
        raw_input: content,
        input_mode: mode,
      });
      setMessages((m) =>
        m.map((msg) =>
          msg.id === typingId
            ? {
                id: typingId,
                role: "assistant",
                content: res.guest_reply,
                raised: res.kind === "service_request",
              }
            : msg,
        ),
      );
    } catch (err) {
      setMessages((m) =>
        m.map((msg) =>
          msg.id === typingId
            ? {
                id: typingId,
                role: "assistant",
                content:
                  "Sorry — I couldn't process that just now. Please try again.",
              }
            : msg,
        ),
      );
      toast.error(
        err instanceof ApiError ? err.message : "Something went wrong.",
      );
    } finally {
      setSending(false);
    }
  }

  async function handleVoice(blob: Blob) {
    setShowVoice(false);
    if (!token) return;
    setTranscribing(true);
    try {
      const { text } = await api.ai.transcribe(token, blob);
      if (text.trim()) await send(text, "voice");
      else toast.error("Didn't catch that — please try again.");
    } catch {
      toast.error("Couldn't transcribe the audio. Please try again.");
    } finally {
      setTranscribing(false);
    }
  }

  const firstName = guest?.guest_name.split(" ")[0] ?? "there";
  const showWelcome = loaded && messages.length === 0;

  return (
    <div className="relative flex min-h-0 flex-1 flex-col">
      <header className="flex items-center justify-between border-b border-white/8 px-5 py-3.5">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-cream">AI Concierge</span>
          <span className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            Online
          </span>
        </div>
        <span className="text-xs text-muted-foreground">
          Room {guest?.room_number}
        </span>
      </header>

      <div
        ref={scrollRef}
        className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto px-4 py-4"
      >
        {!loaded && (
          <div className="m-auto flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading your chat…
          </div>
        )}

        {showWelcome && (
          <Bubble
            msg={{
              id: "welcome",
              role: "assistant",
              content: `Hello ${firstName}! I'm your personal concierge for room ${guest?.room_number}. How can I help you today?`,
            }}
            slug={params.slug}
          />
        )}

        <AnimatePresence initial={false}>
          {messages.map((m) => (
            <Bubble key={m.id} msg={m} slug={params.slug} />
          ))}
        </AnimatePresence>
      </div>

      {/* Suggested prompts */}
      <div className="flex gap-2 overflow-x-auto px-4 pb-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {CHIPS.map((chip) => (
          <button
            key={chip}
            disabled={sending}
            onClick={() => send(chip, "chip")}
            className="shrink-0 rounded-full border border-white/15 bg-white/[0.06] px-3.5 py-1.5 text-xs text-cream/80 transition-colors hover:border-gold/50 hover:text-gold disabled:opacity-50"
          >
            {chip}
          </button>
        ))}
      </div>

      {/* Input row */}
      <div className="flex items-center gap-2 border-t border-white/8 px-4 py-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") send(input, "text");
          }}
          disabled={sending || transcribing}
          placeholder={transcribing ? "Transcribing…" : "Type your request…"}
          className="h-11 flex-1 rounded-full border border-white/15 bg-white/[0.07] px-4 text-sm text-cream outline-none placeholder:text-cream/30 focus:border-gold/50 disabled:opacity-60"
        />
        <button
          onClick={() => setShowVoice(true)}
          disabled={sending || transcribing}
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-gold text-navy disabled:opacity-50"
          aria-label="Record voice note"
        >
          {transcribing ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <Mic className="h-5 w-5" />
          )}
        </button>
        <button
          onClick={() => send(input, "text")}
          disabled={sending || transcribing || !input.trim()}
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-white/10 text-gold disabled:opacity-40"
          aria-label="Send"
        >
          <Send className="h-[18px] w-[18px]" />
        </button>
      </div>

      {showVoice && (
        <VoiceRecorder onResult={handleVoice} onCancel={() => setShowVoice(false)} />
      )}
    </div>
  );
}

function Bubble({ msg, slug }: { msg: ChatMsg; slug: string }) {
  const isGuest = msg.role === "guest";
  return (
    <motion.div
      initial={{ opacity: 0, y: 8, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 400, damping: 30 }}
      className={cn("flex max-w-[82%] flex-col gap-1", isGuest ? "self-end items-end" : "self-start items-start")}
    >
      <div
        className={cn(
          "rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
          isGuest
            ? "rounded-br-md bg-gold font-medium text-navy"
            : "rounded-bl-md border border-white/10 bg-white/[0.08] text-cream",
        )}
      >
        {msg.pending ? <TypingDots /> : msg.content}
      </div>
      {msg.raised && (
        <Link
          href={`/h/${slug}/requests`}
          className="flex items-center gap-1 rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-300"
        >
          <CheckCircle2 className="h-3 w-3" /> Request raised · track it
        </Link>
      )}
    </motion.div>
  );
}

function TypingDots() {
  return (
    <span className="flex items-center gap-1 py-1">
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="h-1.5 w-1.5 rounded-full bg-cream/60"
          animate={{ y: [0, -4, 0] }}
          transition={{ duration: 0.9, repeat: Infinity, delay: i * 0.15 }}
        />
      ))}
    </span>
  );
}
