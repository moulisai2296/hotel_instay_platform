/**
 * Public env access. Only NEXT_PUBLIC_* vars are available in the browser.
 * Never reference SUPABASE_SERVICE_ROLE_KEY here — backend-only.
 */

function required(name: string, value: string | undefined): string {
  if (!value) {
    // Surface misconfig loudly in dev; in prod the build will have inlined these.
    if (process.env.NODE_ENV !== "production") {
      // eslint-disable-next-line no-console
      console.warn(`[env] Missing ${name} — check apps/web/.env.local`);
    }
    return "";
  }
  return value;
}

export const env = {
  apiBaseUrl: required(
    "NEXT_PUBLIC_API_BASE_URL",
    process.env.NEXT_PUBLIC_API_BASE_URL,
  ),
  supabaseUrl: required(
    "NEXT_PUBLIC_SUPABASE_URL",
    process.env.NEXT_PUBLIC_SUPABASE_URL,
  ),
  supabaseAnonKey: required(
    "NEXT_PUBLIC_SUPABASE_ANON_KEY",
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  ),
} as const;
