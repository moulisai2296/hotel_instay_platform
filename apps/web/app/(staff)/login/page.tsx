"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import { ArrowLeft, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Wordmark } from "@/components/brand/wordmark";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useStaffStore } from "@/stores/staff-store";
import { ApiError } from "@/lib/api-client";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

type FormValues = z.infer<typeof schema>;

export default function StaffLoginPage() {
  const router = useRouter();
  const login = useStaffStore((s) => s.login);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    try {
      await login(values.email, values.password);
      toast.success("Welcome back");
      router.replace("/dashboard");
    } catch (err) {
      const message =
        err instanceof ApiError && err.status === 401
          ? "Incorrect email or password."
          : err instanceof ApiError && err.status === 403
            ? "This account has been deactivated. Contact your admin."
            : "Couldn't sign in. Please try again.";
      toast.error(message);
    }
  };

  return (
    <main className="relative flex min-h-dvh items-center justify-center bg-stone px-6 py-12">
      <Link
        href="/"
        className="absolute left-5 top-5 flex h-9 w-9 items-center justify-center rounded-full border border-border bg-card text-muted-foreground transition-colors hover:text-foreground"
        aria-label="Back"
      >
        <ArrowLeft className="h-4 w-4" />
      </Link>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-sm"
      >
        <div className="overflow-hidden rounded-3xl border border-border bg-card shadow-card">
          <div className="bg-navy px-8 py-7 text-center">
            <Wordmark className="text-2xl" tone="dark" />
            <p className="mt-1 text-xs text-cream/50">Staff &amp; management portal</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 p-8">
            <div>
              <h1 className="text-lg font-bold text-foreground">Welcome back</h1>
              <p className="text-sm text-muted-foreground">
                Sign in to your dashboard
              </p>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="you@hotel.com"
                {...register("email")}
              />
              {errors.email && (
                <p className="text-xs text-destructive">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                placeholder="••••••••"
                {...register("password")}
              />
              {errors.password && (
                <p className="text-xs text-destructive">
                  {errors.password.message}
                </p>
              )}
            </div>

            <Button
              type="submit"
              disabled={isSubmitting}
              className="h-11 w-full bg-navy text-cream hover:bg-navy-800"
            >
              {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Sign in
            </Button>

            <p className="text-center text-xs text-muted-foreground">
              Staff accounts are provisioned by your admin.
            </p>
          </form>
        </div>
      </motion.div>
    </main>
  );
}
