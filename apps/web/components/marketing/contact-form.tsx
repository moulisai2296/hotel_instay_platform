"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import { Loader2, CheckCircle2, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const schema = z.object({
  name: z.string().min(1, "Your name is required"),
  hotel: z.string().min(1, "Hotel name is required"),
  email: z.string().email("Enter a valid email"),
  message: z.string().min(1, "Tell us a little about your property"),
});
type FormValues = z.infer<typeof schema>;

const inputCls =
  "border-white/15 bg-white/[0.05] text-cream placeholder:text-cream/30 focus-visible:ring-gold";

/**
 * Marketing contact form. Currently client-only: validates and confirms.
 * TODO: wire to an email/CRM endpoint (e.g. a /contact API route or a form
 * service) — no backend handler exists yet.
 */
export function ContactForm() {
  const [sent, setSent] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async () => {
    // TODO: POST to an email/CRM endpoint. For now, confirm client-side.
    await new Promise((r) => setTimeout(r, 700));
    setSent(true);
  };

  if (sent) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center gap-3 rounded-2xl border border-gold/30 bg-gold/[0.06] p-8 text-center"
      >
        <CheckCircle2 className="h-10 w-10 text-gold" />
        <h3 className="font-display text-xl font-bold text-cream">Thank you!</h3>
        <p className="max-w-sm text-sm text-cream/60">
          We&apos;ve got your details and a member of our team will reach out shortly
          to set up your personalized walkthrough.
        </p>
      </motion.div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Your name" error={errors.name?.message}>
          <Input className={inputCls} placeholder="Asha Rao" {...register("name")} />
        </Field>
        <Field label="Hotel / group" error={errors.hotel?.message}>
          <Input className={inputCls} placeholder="The Grand Horizon" {...register("hotel")} />
        </Field>
      </div>
      <Field label="Work email" error={errors.email?.message}>
        <Input className={inputCls} type="email" placeholder="you@hotel.com" {...register("email")} />
      </Field>
      <Field label="What would you like to improve?" error={errors.message?.message}>
        <textarea
          rows={4}
          placeholder="We want faster guest service and better visibility into our operations…"
          className={`w-full rounded-md border ${inputCls} px-3 py-2 text-sm outline-none`}
          {...register("message")}
        />
      </Field>
      <Button
        type="submit"
        disabled={isSubmitting}
        className="h-11 w-full bg-gold text-navy hover:bg-gold-400"
      >
        {isSubmitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Send className="mr-2 h-4 w-4" />}
        Book a demo
      </Button>
    </form>
  );
}

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-cream/70">{label}</Label>
      {children}
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}
