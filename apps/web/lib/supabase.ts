/**
 * Browser Supabase client for the direct-from-Supabase reads + realtime
 * (docs/API.md §6). Uses the ANON key only — never the service-role key — and
 * authenticates each request with the app JWT so RLS sees `session_id`/`hotel_id`.
 *
 * Writes do NOT go here; they go through lib/api-client.ts (FastAPI).
 */
import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import { env } from "./env";

export type TokenGetter = () => string | null | undefined;

/**
 * Build a Supabase client whose every request carries the current app JWT.
 * Pass a getter (not a static token) so it always reflects the live session
 * from the Zustand auth store, even after refresh.
 */
export function createSupabaseClient(getToken: TokenGetter): SupabaseClient {
  return createClient(env.supabaseUrl, env.supabaseAnonKey, {
    accessToken: async () => getToken() ?? null,
    auth: {
      persistSession: false,
      autoRefreshToken: false,
    },
  });
}
