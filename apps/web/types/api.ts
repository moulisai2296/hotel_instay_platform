/**
 * API & domain types — mirror of docs/API.md (backend as implemented, Step 6).
 * Keep enums in sync with §7 "Enum reference".
 */

export type AppRole =
  | "staff"
  | "dept_manager"
  | "hotel_manager"
  | "admin"
  | "guest";

export type DepartmentType =
  | "housekeeping"
  | "fb"
  | "maintenance"
  | "concierge"
  | "spa"
  | "front_desk";

export type RequestStatus =
  | "pending"
  | "assigned"
  | "in_progress"
  | "completed"
  | "escalated"
  | "cancelled";

export type RequestPriority = "low" | "medium" | "high" | "urgent";

export type InputMode = "text" | "voice" | "chip";

export type IntentKind = "service_request" | "needs_info" | "unsupported";

/** Machine codes the UI is expected to handle (docs/API.md §2). */
export type ApiErrorCode =
  | "NOT_AUTHENTICATED"
  | "INVALID_TOKEN"
  | "INVALID_CREDENTIALS"
  | "GUEST_ONLY"
  | "HOTEL_MISMATCH"
  | "MODE_DISABLED"
  | "NO_DEPARTMENT"
  | "VALIDATION_ERROR"
  | "RATE_LIMITED"
  | "UNKNOWN";

// ── Auth ────────────────────────────────────────────────────────────────────

export interface AuthTokens {
  access_token: string;
  refresh_token?: string;
  token_type: "bearer";
}

export interface StaffProfile {
  id: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  role: Exclude<AppRole, "guest">;
  display_name: string | null;
  hotel_id: string;
  department_id: string | null;
  avatar_url: string | null;
  last_seen_at: string | null;
}

export interface GuestVerifyRequest {
  hotel_slug: string;
  room_number: string;
  pin: string;
}

export interface GuestSummary {
  session_id: string;
  guest_name: string;
  room_number: string;
  hotel_id: string;
  checkout_date: string;
}

export interface GuestVerifyResponse {
  access_token: string;
  token_type: "bearer";
  expires_at: string;
  guest: GuestSummary;
}

export interface GuestProfile {
  session_id: string;
  hotel_id: string;
  room_id: string;
  app_role: "guest";
}

// ── Requests (guest chat turn) ───────────────────────────────────────────────

export interface ExtractedItem {
  item: string;
  qty: number;
}

export interface RequestRecord {
  id: string;
  status: RequestStatus;
  priority: RequestPriority;
  department_id: string;
  ai_title: string;
  items: ExtractedItem[];
  sentiment: number;
  created_at: string;
}

export interface CreateRequestBody {
  raw_input: string;
  input_mode: InputMode;
  voice_url?: string | null;
}

export interface CreateRequestResponse {
  kind: IntentKind;
  guest_reply: string;
  request: RequestRecord | null;
}

export interface TranscribeResponse {
  text: string;
}
