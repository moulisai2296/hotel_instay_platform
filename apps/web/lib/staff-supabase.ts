/**
 * Singleton Supabase client for the staff dashboards. Authenticated with the
 * live staff JWT from the Zustand store, so RLS scopes reads + realtime to the
 * staff member's hotel (and department, for staff/dept_manager).
 *
 * Reads + realtime only — status writes go through lib/api-client.ts (FastAPI).
 */
import type { SupabaseClient } from "@supabase/supabase-js";
import { createSupabaseClient } from "./supabase";
import { useStaffStore } from "@/stores/staff-store";

let client: SupabaseClient | null = null;

export function getStaffSupabase(): SupabaseClient {
  if (!client) {
    client = createSupabaseClient(() => useStaffStore.getState().token);
  }
  return client;
}
