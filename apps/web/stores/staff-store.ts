/**
 * Staff / Manager / Admin session store. The backend also sets HTTP-only
 * cookies on login; we keep the access token in sessionStorage so Bearer calls
 * work after a reload within the tab. Profile (role, hotel, department) drives
 * dashboard routing in PR 3.
 */
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { api } from "@/lib/api-client";
import type { StaffProfile } from "@/types/api";

interface StaffState {
  token: string | null;
  profile: StaffProfile | null;
  hasHydrated: boolean;

  login: (email: string, password: string) => Promise<StaffProfile>;
  loadProfile: () => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: () => boolean;
  setHasHydrated: (v: boolean) => void;
}

export const useStaffStore = create<StaffState>()(
  persist(
    (set, get) => ({
      token: null,
      profile: null,
      hasHydrated: false,

      login: async (email, password) => {
        const tokens = await api.auth.login(email, password);
        set({ token: tokens.access_token });
        const profile = await api.auth.me(tokens.access_token);
        set({ profile });
        return profile;
      },

      loadProfile: async () => {
        const { token } = get();
        if (!token) return;
        const profile = await api.auth.me(token);
        set({ profile });
      },

      logout: async () => {
        const { token } = get();
        try {
          await api.auth.logout(token);
        } finally {
          set({ token: null, profile: null });
        }
      },

      isAuthenticated: () => Boolean(get().token),

      setHasHydrated: (v) => set({ hasHydrated: v }),
    }),
    {
      name: "instayos-staff",
      storage: createJSONStorage(() => sessionStorage),
      partialize: (s) => ({ token: s.token, profile: s.profile }),
      onRehydrateStorage: () => (state) => state?.setHasHydrated(true),
    },
  ),
);
