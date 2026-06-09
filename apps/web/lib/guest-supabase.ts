/**
 * Singleton Supabase client for the guest app. Authenticated with the live
 * guest JWT from the Zustand store (read fresh on every request/subscription),
 * so RLS scopes all reads + realtime to the guest's own session.
 *
 * Reads + realtime only — writes go through lib/api-client.ts (FastAPI).
 */
import type { SupabaseClient } from "@supabase/supabase-js";
import { createSupabaseClient } from "./supabase";
import { useGuestStore } from "@/stores/guest-store";

let client: SupabaseClient | null = null;

export function getGuestSupabase(): SupabaseClient {
  if (!client) {
    client = createSupabaseClient(() => useGuestStore.getState().token);
  }
  return client;
}
