/**
 * Guest session store (custom PIN flow). Token is persisted to **sessionStorage
 * only** — never localStorage (CLAUDE.md / docs/API.md §4). Cleared on tab close
 * and at checkout expiry.
 */
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { api, ApiError } from "@/lib/api-client";
import type { GuestSummary, GuestVerifyRequest } from "@/types/api";

interface GuestState {
  token: string | null;
  expiresAt: string | null;
  guest: GuestSummary | null;
  hotelSlug: string | null;
  hasHydrated: boolean;

  verifyPin: (input: GuestVerifyRequest) => Promise<void>;
  logout: () => void;
  /** True when a non-expired guest token is held. */
  isAuthenticated: () => boolean;
  setHasHydrated: (v: boolean) => void;
}

export const useGuestStore = create<GuestState>()(
  persist(
    (set, get) => ({
      token: null,
      expiresAt: null,
      guest: null,
      hotelSlug: null,
      hasHydrated: false,

      verifyPin: async (input) => {
        const res = await api.guest.verifyPin(input);
        set({
          token: res.access_token,
          expiresAt: res.expires_at,
          guest: res.guest,
          hotelSlug: input.hotel_slug,
        });
      },

      logout: () =>
        set({ token: null, expiresAt: null, guest: null, hotelSlug: null }),

      isAuthenticated: () => {
        const { token, expiresAt } = get();
        if (!token) return false;
        if (expiresAt && Date.parse(expiresAt) <= Date.now()) return false;
        return true;
      },

      setHasHydrated: (v) => set({ hasHydrated: v }),
    }),
    {
      name: "instayos-guest",
      storage: createJSONStorage(() => sessionStorage),
      partialize: (s) => ({
        token: s.token,
        expiresAt: s.expiresAt,
        guest: s.guest,
        hotelSlug: s.hotelSlug,
      }),
      onRehydrateStorage: () => (state) => state?.setHasHydrated(true),
    },
  ),
);

export { ApiError };
