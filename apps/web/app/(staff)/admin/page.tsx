"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import { Loader2, KeyRound, Copy, Check, UserPlus, BedDouble, Users } from "lucide-react";
import { toast } from "sonner";
import { TopBar, navForRole, ROLE_LABEL } from "@/components/staff/top-bar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useStaffGuard } from "@/hooks/use-staff-guard";
import { useStaffStore } from "@/stores/staff-store";
import { getStaffSupabase } from "@/lib/staff-supabase";
import { api, ApiError } from "@/lib/api-client";
import type { CreateGuestSessionResult } from "@/types/api";

const schema = z.object({
  room_number: z.string().min(1, "Room is required"),
  guest_name: z.string().min(1, "Guest name is required"),
  checkout_date: z.string().min(1, "Checkout date is required"),
  num_guests: z.number().int().min(1).max(20),
});
type FormValues = z.infer<typeof schema>;

interface GuestRow {
  id: string;
  guest_name: string;
  checkin_date: string;
  checkout_date: string;
  room: { room_number: string } | { room_number: string }[] | null;
}
interface TeamRow {
  id: string;
  display_name: string | null;
  email: string;
  role: string;
}

const roomOf = (g: GuestRow) =>
  (Array.isArray(g.room) ? g.room[0]?.room_number : g.room?.room_number) ?? "—";

const tomorrow = () => {
  const d = new Date(Date.now() + 864e5);
  return d.toISOString().slice(0, 10);
};

export default function AdminPage() {
  const router = useRouter();
  const { ready, profile } = useStaffGuard();
  const token = useStaffStore((s) => s.token);
  const isManager = profile?.role === "hotel_manager" || profile?.role === "admin";

  const [guests, setGuests] = useState<GuestRow[] | null>(null);
  const [team, setTeam] = useState<TeamRow[]>([]);
  const [result, setResult] = useState<CreateGuestSessionResult | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (ready && profile && !isManager) router.replace("/dashboard");
  }, [ready, profile, isManager, router]);

  const loadGuests = useCallback(async () => {
    const supabase = getStaffSupabase();
    const { data } = await supabase
      .from("guest_sessions")
      .select("id, guest_name, checkin_date, checkout_date, room:rooms(room_number)")
      .eq("is_checked_out", false)
      .order("checkin_date", { ascending: false });
    setGuests((data ?? []) as GuestRow[]);
  }, []);

  useEffect(() => {
    if (!isManager) return;
    loadGuests();
    getStaffSupabase()
      .from("users")
      .select("id, display_name, email, role")
      .then(({ data }) => setTeam((data ?? []) as TeamRow[]));
  }, [isManager, loadGuests]);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { checkout_date: tomorrow(), num_guests: 1 },
  });

  const onSubmit = async (values: FormValues) => {
    if (!token) return;
    try {
      const res = await api.admin.checkIn(token, {
        room_number: values.room_number,
        guest_name: values.guest_name,
        checkout_date: values.checkout_date,
        num_guests: values.num_guests || 1,
      });
      setResult(res);
      setCopied(false);
      toast.success(`${res.guest_name} checked in to room ${res.room_number}`);
      reset({ checkout_date: tomorrow(), num_guests: 1, room_number: "", guest_name: "" });
      loadGuests();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Check-in failed.");
    }
  };

  if (!ready || !profile || !isManager) {
    return (
      <div className="flex min-h-dvh items-center justify-center text-sm text-muted-foreground">
        Loading…
      </div>
    );
  }

  return (
    <div className="flex min-h-dvh flex-col bg-stone">
      <TopBar nav={navForRole(profile.role)} />
      <main className="mx-auto w-full max-w-5xl flex-1 space-y-5 p-5 md:p-6">
        <div>
          <h1 className="text-xl font-bold text-foreground">Admin</h1>
          <p className="text-sm text-muted-foreground">Check in guests and manage your hotel</p>
        </div>

        <div className="grid gap-5 lg:grid-cols-2">
          {/* Check-in */}
          <section className="rounded-2xl border border-border bg-card p-5 shadow-card">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-bold text-foreground">
              <UserPlus className="h-4 w-4 text-gold" /> Guest check-in
            </h2>

            {result ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.97 }}
                animate={{ opacity: 1, scale: 1 }}
                className="space-y-3 rounded-xl border border-gold/30 bg-gold/[0.06] p-4 text-center"
              >
                <p className="text-sm text-muted-foreground">
                  {result.guest_name} · Room {result.room_number}
                </p>
                <div className="flex items-center justify-center gap-2">
                  <KeyRound className="h-5 w-5 text-gold" />
                  <span className="font-mono text-3xl font-bold tracking-[0.3em] text-foreground">
                    {result.pin}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">
                  Share this PIN with the guest — it won&apos;t be shown again.
                </p>
                <div className="flex justify-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      navigator.clipboard?.writeText(result.pin);
                      setCopied(true);
                    }}
                  >
                    {copied ? <Check className="mr-1 h-4 w-4" /> : <Copy className="mr-1 h-4 w-4" />}
                    {copied ? "Copied" : "Copy PIN"}
                  </Button>
                  <Button size="sm" onClick={() => setResult(null)} className="bg-navy text-cream hover:bg-navy-800">
                    Check in another
                  </Button>
                </div>
              </motion.div>
            ) : (
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label htmlFor="room_number">Room number</Label>
                    <Input id="room_number" placeholder="305" {...register("room_number")} />
                    {errors.room_number && <p className="mt-1 text-xs text-destructive">{errors.room_number.message}</p>}
                  </div>
                  <div>
                    <Label htmlFor="num_guests">Guests</Label>
                    <Input id="num_guests" type="number" min={1} {...register("num_guests", { valueAsNumber: true })} />
                  </div>
                </div>
                <div>
                  <Label htmlFor="guest_name">Guest name</Label>
                  <Input id="guest_name" placeholder="Jane Doe" {...register("guest_name")} />
                  {errors.guest_name && <p className="mt-1 text-xs text-destructive">{errors.guest_name.message}</p>}
                </div>
                <div>
                  <Label htmlFor="checkout_date">Checkout date</Label>
                  <Input id="checkout_date" type="date" {...register("checkout_date")} />
                  {errors.checkout_date && <p className="mt-1 text-xs text-destructive">{errors.checkout_date.message}</p>}
                </div>
                <Button type="submit" disabled={isSubmitting} className="w-full bg-navy text-cream hover:bg-navy-800">
                  {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Check in &amp; generate PIN
                </Button>
              </form>
            )}
          </section>

          {/* In-house guests */}
          <section className="rounded-2xl border border-border bg-card p-5 shadow-card">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-bold text-foreground">
              <BedDouble className="h-4 w-4 text-gold" /> In-house guests
              {guests && <span className="text-xs font-normal text-muted-foreground">({guests.length})</span>}
            </h2>
            {guests === null ? (
              <div className="flex items-center gap-2 py-4 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" /> Loading…
              </div>
            ) : guests.length === 0 ? (
              <p className="py-4 text-sm text-muted-foreground">No active guests. Check one in to get started.</p>
            ) : (
              <div className="max-h-72 space-y-2 overflow-y-auto">
                {guests.map((g) => (
                  <div key={g.id} className="flex items-center justify-between rounded-xl border border-border px-3 py-2">
                    <div>
                      <p className="text-sm font-semibold text-foreground">{g.guest_name}</p>
                      <p className="text-[11px] text-muted-foreground">
                        Until {new Date(g.checkout_date).toLocaleDateString()}
                      </p>
                    </div>
                    <Badge className="bg-navy/10 text-navy hover:bg-navy/10">Room {roomOf(g)}</Badge>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>

        {/* Team */}
        <section className="rounded-2xl border border-border bg-card p-5 shadow-card">
          <h2 className="mb-3 flex items-center gap-2 text-sm font-bold text-foreground">
            <Users className="h-4 w-4 text-gold" /> Team
            <span className="text-xs font-normal text-muted-foreground">({team.length})</span>
          </h2>
          <div className="grid gap-2 sm:grid-cols-2">
            {team.map((u) => (
              <div key={u.id} className="flex items-center justify-between rounded-xl border border-border px-3 py-2">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-foreground">{u.display_name ?? u.email}</p>
                  <p className="truncate text-[11px] text-muted-foreground">{u.email}</p>
                </div>
                <Badge className="shrink-0 bg-stone-surface text-muted-foreground hover:bg-stone-surface">
                  {ROLE_LABEL[u.role] ?? u.role}
                </Badge>
              </div>
            ))}
          </div>
          <p className="mt-4 text-center text-[11px] text-muted-foreground">
            User provisioning, tablets &amp; PMS integration are on the roadmap.
          </p>
        </section>
      </main>
    </div>
  );
}
