"use client";

import { useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Bot,
  LayoutDashboard,
  BarChart3,
  KeyRound,
  ArrowRight,
  Play,
  Sparkles,
  Mic,
  MessageSquare,
  Smile,
  Tag,
  DoorOpen,
} from "lucide-react";
import { Wordmark } from "@/components/brand/wordmark";
import { Aurora } from "@/components/brand/aurora";
import { TiltCard } from "@/components/marketing/tilt-card";
import { PhoneMockup } from "@/components/marketing/phone-mockup";
import { ContactForm } from "@/components/marketing/contact-form";

const NAV = [
  { label: "Product", href: "#product" },
  { label: "Outcomes", href: "#outcomes" },
  { label: "Insights", href: "#insights" },
  { label: "About", href: "#about" },
];

const FEATURES = [
  {
    Icon: Bot,
    title: "AI Concierge",
    body: "Guests ask in plain language — by text or voice. Every request is understood, routed to the right team, and answered in seconds.",
  },
  {
    Icon: LayoutDashboard,
    title: "Real-time operations",
    body: "A live board for every department. Staff see new requests the moment they land and move them to done in a tap.",
  },
  {
    Icon: BarChart3,
    title: "Manager insight",
    body: "Response times, department load, escalations and satisfaction — your whole property at a glance, updating live.",
  },
  {
    Icon: KeyRound,
    title: "Effortless check-in",
    body: "The front desk issues a room + PIN. Guests open the experience on their own phone — no app store, no tablets.",
  },
];

const STATS = [
  { value: "0", label: "App downloads — it runs in the browser" },
  { value: "24/7", label: "AI concierge, in any language" },
  { value: "Live", label: "Operations board for every team" },
  { value: "1", label: "Platform for guest, staff, manager & admin" },
];

const JOURNEY = [
  { Icon: KeyRound, label: "Check-in", note: "Room + PIN issued" },
  { Icon: MessageSquare, label: "Requests", note: "Every ask captured" },
  { Icon: Smile, label: "Sentiment", note: "Tone scored per message" },
  { Icon: Tag, label: "Offers", note: "Upsells & uptake" },
  { Icon: DoorOpen, label: "Checkout", note: "Ratings & resolution time" },
];

function Reveal({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.5, delay }}
    >
      {children}
    </motion.div>
  );
}

export default function LandingPage() {
  useEffect(() => {
    document.documentElement.classList.add("scroll-smooth");
    return () => document.documentElement.classList.remove("scroll-smooth");
  }, []);

  return (
    <div className="min-h-dvh bg-navy-900 font-sans text-cream">
      {/* NAV */}
      <header className="sticky top-0 z-50 border-b border-white/8 bg-navy-900/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3.5">
          <Wordmark className="text-xl" />
          <nav className="hidden items-center gap-7 md:flex">
            {NAV.map((n) => (
              <a key={n.href} href={n.href} className="text-sm text-cream/60 transition-colors hover:text-cream">
                {n.label}
              </a>
            ))}
          </nav>
          <div className="flex items-center gap-2">
            <Link href="/" className="hidden rounded-full px-4 py-2 text-sm text-cream/70 transition-colors hover:text-cream sm:block">
              Open app
            </Link>
            <a href="#contact" className="rounded-full bg-gold px-4 py-2 text-sm font-semibold text-navy transition-transform hover:scale-[1.03]">
              Book a demo
            </a>
          </div>
        </div>
      </header>

      {/* HERO */}
      <section className="relative overflow-hidden">
        <Aurora />
        <div className="relative z-10 mx-auto grid max-w-6xl items-center gap-12 px-5 py-20 md:grid-cols-2 md:py-28">
          <div>
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="mb-5 inline-flex items-center gap-2 rounded-full border border-gold/30 bg-gold/10 px-3 py-1 text-xs font-medium text-gold"
            >
              <Sparkles className="h-3.5 w-3.5" /> AI-powered in-stay experience
            </motion.div>
            <motion.h1
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.05 }}
              className="font-display text-4xl font-bold leading-[1.1] text-cream md:text-6xl"
            >
              The in-stay experience your guests <span className="text-gold">remember</span>.
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.12 }}
              className="mt-5 max-w-md text-lg text-cream/60"
            >
              InStayOS turns every guest request into instant action and every interaction
              into insight — from check-in to checkout, on the guest&apos;s own phone.
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.18 }}
              className="mt-8 flex flex-wrap items-center gap-3"
            >
              <a href="#contact" className="group flex items-center gap-2 rounded-full bg-gold px-6 py-3 font-semibold text-navy transition-transform hover:scale-[1.03]">
                Book a demo <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </a>
              <a href="#product" className="rounded-full border border-white/15 px-6 py-3 font-semibold text-cream transition-colors hover:border-gold/50">
                See how it works
              </a>
            </motion.div>
          </div>

          <div className="flex justify-center">
            <PhoneMockup />
          </div>
        </div>
      </section>

      {/* PRODUCT / OFFER */}
      <section id="product" className="scroll-mt-24 border-t border-white/8 bg-navy py-20 md:py-24">
        <div className="mx-auto max-w-6xl px-5">
          <Reveal>
            <p className="text-sm font-semibold uppercase tracking-[0.15em] text-gold/70">What we offer</p>
            <h2 className="mt-2 max-w-2xl font-display text-3xl font-bold text-cream md:text-4xl">
              One platform for the whole stay — and the whole team.
            </h2>
          </Reveal>
          <div className="mt-12 grid gap-5 sm:grid-cols-2">
            {FEATURES.map((f, i) => (
              <Reveal key={f.title} delay={i * 0.06}>
                <TiltCard className="h-full rounded-2xl border border-white/10 bg-white/[0.04] p-6 transition-colors hover:border-gold/40">
                  <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gold/15 text-gold [transform:translateZ(40px)]">
                    <f.Icon className="h-6 w-6" />
                  </div>
                  <h3 className="text-lg font-bold text-cream">{f.title}</h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-cream/55">{f.body}</p>
                </TiltCard>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* OUTCOMES */}
      <section id="outcomes" className="scroll-mt-24 bg-stone py-20 text-navy md:py-24">
        <div className="mx-auto max-w-6xl px-5">
          <Reveal>
            <p className="text-sm font-semibold uppercase tracking-[0.15em] text-gold">The outcome</p>
            <h2 className="mt-2 max-w-2xl font-display text-3xl font-bold md:text-4xl">
              Faster service, happier guests, a lighter front desk.
            </h2>
            <p className="mt-3 max-w-xl text-navy/60">
              When requests route themselves and your team works from one live board, guests
              wait less, staff do more of the hospitality that matters, and nothing slips.
            </p>
          </Reveal>
          <div className="mt-12 grid grid-cols-2 gap-4 lg:grid-cols-4">
            {STATS.map((s, i) => (
              <Reveal key={s.label} delay={i * 0.06}>
                <div className="rounded-2xl border border-navy/10 bg-white p-6 text-center shadow-card">
                  <div className="font-display text-4xl font-bold text-navy">{s.value}</div>
                  <p className="mt-2 text-xs text-navy/55">{s.label}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* INSIGHTS — customer journey analytics */}
      <section id="insights" className="scroll-mt-24 bg-navy py-20 md:py-24">
        <div className="mx-auto max-w-6xl px-5">
          <Reveal>
            <p className="text-sm font-semibold uppercase tracking-[0.15em] text-gold/70">Customer-journey analytics</p>
            <h2 className="mt-2 max-w-2xl font-display text-3xl font-bold text-cream md:text-4xl">
              Every tap, message and moment becomes data you can act on.
            </h2>
            <p className="mt-3 max-w-2xl text-cream/55">
              InStayOS quietly records every request, conversation, sentiment signal and
              response time across the stay. The result is a complete, structured picture of
              the guest journey — so you can see exactly where you delight or disappoint, and
              fix it before checkout.
            </p>
          </Reveal>

          <Reveal delay={0.1}>
            <div className="mt-12 rounded-3xl border border-white/10 bg-white/[0.03] p-6 md:p-10">
              <div className="grid gap-4 md:grid-cols-5">
                {JOURNEY.map((j, i) => (
                  <div key={j.label} className="relative">
                    <div className="flex flex-col items-center text-center">
                      <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-gold/30 bg-gold/10 text-gold">
                        <j.Icon className="h-6 w-6" />
                      </div>
                      <p className="mt-3 text-sm font-bold text-cream">{j.label}</p>
                      <p className="text-[11px] text-cream/45">{j.note}</p>
                    </div>
                    {i < JOURNEY.length - 1 && (
                      <div className="absolute right-[-0.5rem] top-7 hidden h-px w-[calc(50%)] bg-gradient-to-r from-gold/40 to-transparent md:block" />
                    )}
                  </div>
                ))}
              </div>
              <div className="mt-8 grid gap-3 border-t border-white/10 pt-6 sm:grid-cols-3">
                {[
                  "Resolution time per request & department",
                  "Sentiment trend across the whole stay",
                  "Offer uptake & in-stay revenue",
                ].map((m) => (
                  <div key={m} className="flex items-start gap-2 text-sm text-cream/70">
                    <BarChart3 className="mt-0.5 h-4 w-4 shrink-0 text-gold" /> {m}
                  </div>
                ))}
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* VIDEO placeholder (future demo) */}
      <section className="bg-navy-900 py-20 md:py-24">
        <div className="mx-auto max-w-4xl px-5 text-center">
          <Reveal>
            <h2 className="font-display text-3xl font-bold text-cream md:text-4xl">See it in action</h2>
            <p className="mx-auto mt-3 max-w-lg text-cream/55">
              A guided tour through the guest, staff, manager and admin experience.
            </p>
            <div className="group relative mt-8 flex aspect-video items-center justify-center overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-navy-800 to-navy-700">
              <Aurora />
              <button className="relative z-10 flex h-20 w-20 items-center justify-center rounded-full bg-gold text-navy shadow-glow transition-transform group-hover:scale-105">
                <Play className="ml-1 h-8 w-8 fill-navy" />
              </button>
              <span className="absolute bottom-4 right-5 z-10 text-xs text-cream/40">Demo video coming soon</span>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ABOUT */}
      <section id="about" className="scroll-mt-24 bg-stone py-20 text-navy md:py-24">
        <div className="mx-auto grid max-w-6xl items-center gap-10 px-5 md:grid-cols-2">
          <Reveal>
            <p className="text-sm font-semibold uppercase tracking-[0.15em] text-gold">About InStayOS</p>
            <h2 className="mt-2 font-display text-3xl font-bold md:text-4xl">
              Built for hospitality, obsessed with the guest.
            </h2>
            <p className="mt-4 text-navy/65">
              Hotels run on a thousand small moments — a towel, a late checkout, a dinner
              booking. InStayOS makes each one effortless for the guest and instant for the
              team, while turning the whole journey into data that helps you get better every
              single stay.
            </p>
            <p className="mt-3 text-navy/65">
              Multi-role, AI-native and mobile-first — one elegant platform that your guests
              love and your staff actually want to use.
            </p>
          </Reveal>
          <Reveal delay={0.1}>
            <div className="grid grid-cols-2 gap-4">
              {[
                ["Guest", "Chat, voice & live request tracking"],
                ["Staff", "A live queue, done in a tap"],
                ["Manager", "Overview, load & alerts"],
                ["Admin", "Check-in, PINs & team"],
              ].map(([role, note]) => (
                <div key={role} className="rounded-2xl border border-navy/10 bg-white p-5 shadow-card">
                  <p className="font-display text-lg font-bold text-navy">{role}</p>
                  <p className="mt-1 text-xs text-navy/55">{note}</p>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      {/* CONTACT */}
      <section id="contact" className="scroll-mt-24 bg-navy py-20 md:py-24">
        <div className="mx-auto grid max-w-5xl items-start gap-12 px-5 md:grid-cols-2">
          <Reveal>
            <h2 className="font-display text-3xl font-bold text-cream md:text-4xl">
              Bring InStayOS to your property.
            </h2>
            <p className="mt-3 text-cream/60">
              Tell us about your hotel and we&apos;ll set up a personalized walkthrough —
              guest app, staff board, manager analytics and admin, end to end.
            </p>
            <div className="mt-8 space-y-3 text-sm text-cream/55">
              <p className="flex items-center gap-2"><Mic className="h-4 w-4 text-gold" /> Voice & text concierge in any language</p>
              <p className="flex items-center gap-2"><LayoutDashboard className="h-4 w-4 text-gold" /> Live for every department</p>
              <p className="flex items-center gap-2"><BarChart3 className="h-4 w-4 text-gold" /> Journey analytics from day one</p>
            </div>
          </Reveal>
          <Reveal delay={0.1}>
            <ContactForm />
          </Reveal>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-white/8 bg-navy-900 py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-5 sm:flex-row">
          <Wordmark className="text-lg" />
          <p className="text-xs text-cream/40">© {new Date().getFullYear()} InStayOS · Your stay, your way</p>
          <div className="flex gap-5 text-xs text-cream/50">
            <a href="#product" className="hover:text-cream">Product</a>
            <a href="#about" className="hover:text-cream">About</a>
            <a href="#contact" className="hover:text-cream">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
