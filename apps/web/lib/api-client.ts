/**
 * The single entry point for all REST calls to the FastAPI backend.
 * Components/stores MUST go through here (CLAUDE.md: "All API calls go through
 * /lib/api-client.ts — never fetch directly in components").
 *
 * Covers writes + AI/aggregation reads. "My rows" lists + realtime go straight
 * to Supabase (see lib/supabase.ts), per docs/API.md §6.
 */
import { env } from "./env";
import type {
  ApiErrorCode,
  AuthTokens,
  CreateRequestBody,
  CreateRequestResponse,
  GuestProfile,
  GuestVerifyRequest,
  GuestVerifyResponse,
  StaffProfile,
  TranscribeResponse,
} from "@/types/api";

/** Normalised error matching the backend envelope `{ error, code }`. */
export class ApiError extends Error {
  readonly code: ApiErrorCode;
  readonly status: number;
  readonly details?: unknown;
  readonly retryAfter?: number;

  constructor(
    message: string,
    code: ApiErrorCode,
    status: number,
    details?: unknown,
    retryAfter?: number,
  ) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
    this.retryAfter = retryAfter;
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  /** JSON body — ignored when `formData` is provided. */
  body?: unknown;
  /** Multipart body (e.g. voice upload). Sets no Content-Type (browser does). */
  formData?: FormData;
  /** Bearer token (staff or guest JWT). */
  token?: string | null;
  signal?: AbortSignal;
}

async function apiFetch<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, formData, token, signal } = opts;

  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (!formData) headers["Content-Type"] = "application/json";

  let res: Response;
  try {
    res = await fetch(`${env.apiBaseUrl}${path}`, {
      method,
      headers,
      credentials: "include", // staff HTTP-only cookies
      signal,
      body: formData ?? (body !== undefined ? JSON.stringify(body) : undefined),
    });
  } catch (cause) {
    // Network/CORS failure — no response.
    throw new ApiError(
      "Can't reach the server. Check your connection and try again.",
      "UNKNOWN",
      0,
      cause,
    );
  }

  if (res.status === 204) return undefined as T;

  const isJson = res.headers.get("content-type")?.includes("application/json");
  const payload = isJson ? await res.json().catch(() => null) : null;

  if (!res.ok) {
    const code = (payload?.code as ApiErrorCode) ?? "UNKNOWN";
    const message =
      (payload?.error as string) ?? res.statusText ?? "Request failed";
    const retryAfter = Number(res.headers.get("retry-after")) || undefined;
    throw new ApiError(message, code, res.status, payload?.details, retryAfter);
  }

  return payload as T;
}

// ── Staff / Manager / Admin auth (docs/API.md §3) ────────────────────────────

export const api = {
  auth: {
    login: (email: string, password: string) =>
      apiFetch<AuthTokens>("/auth/login", {
        method: "POST",
        body: { email, password },
      }),
    me: (token: string) => apiFetch<StaffProfile>("/auth/me", { token }),
    logout: (token?: string | null) =>
      apiFetch<void>("/auth/logout", { method: "POST", token }),
  },

  // ── Guest auth (custom PIN flow — mobile-first, docs/API.md §4) ────────────
  guest: {
    verifyPin: (input: GuestVerifyRequest) =>
      apiFetch<GuestVerifyResponse>("/guest/verify-pin", {
        method: "POST",
        body: input,
      }),
    me: (token: string) => apiFetch<GuestProfile>("/guest/me", { token }),
  },

  // ── Guest chat + requests (docs/API.md §5) ─────────────────────────────────
  requests: {
    create: (token: string, body: CreateRequestBody) =>
      apiFetch<CreateRequestResponse>("/requests/create", {
        method: "POST",
        token,
        body,
      }),
  },

  ai: {
    transcribe: (token: string, audio: Blob, filename = "voice-note.webm") => {
      const fd = new FormData();
      fd.append("audio", audio, filename);
      return apiFetch<TranscribeResponse>("/ai/transcribe", {
        method: "POST",
        token,
        formData: fd,
      });
    },
  },

  health: () => apiFetch<{ status: string }>("/health"),
};
