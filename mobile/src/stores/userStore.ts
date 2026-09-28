import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from '../services/api';
import { getRefreshToken, getToken, restoreToken, setSignedOutHandler, setTokens } from '../services/authToken';
import { API_V1 } from '../services/config';
import { cache } from '../services/cache';
import { deleteLocalDatabase } from '../db/schema';

export interface UserProfile {
  id: string;
  email: string;
  name?: string | null;
  gender?: string | null;
  age?: number | null;
  height_cm?: number | null;
  fitness_level?: string;
  primary_goal?: string;
  preferred_days_per_week?: number;
  work_start?: string | null;
  work_end?: string | null;
}

interface UserStore {
  /** The signed-in account's id; empty when signed out. */
  userId: string;
  /** A session token is stored. Without one the app shows sign-in. */
  signedIn: boolean;
  /** Cached profile from the backend. */
  profile: UserProfile | null;
  hydrated: boolean;
  /** True while we are loading the persisted identity. */
  loading: boolean;
  hydrate: () => Promise<void>;
  setUser: (user: UserProfile) => Promise<void>;
  refreshProfile: () => Promise<void>;
  updateProfile: (patch: Record<string, any>) => Promise<void>;
  clearUser: () => Promise<void>;
}

const STORAGE_KEY = '@adapfit/user_id';

export const useUserStore = create<UserStore>((set, get) => ({
  userId: '',
  signedIn: false,
  profile: null,
  hydrated: false,
  loading: true,

  hydrate: async () => {
    // Must land before the profile fetch below, which needs the header.
    await restoreToken();
    setSignedOutHandler(() => {
      get().clearUser();
    });
    try {
      const userId = (await AsyncStorage.getItem(STORAGE_KEY)) || '';
      if (!getToken() || !userId) {
        set({ userId: '', signedIn: false, profile: null, hydrated: true, loading: false });
        return;
      }
      set({ userId, signedIn: true, hydrated: true });
      // A missing profile row sends the user to onboarding; an unreachable
      // server keeps them in the app on the account id alone.
      api
        .getUser(userId)
        .then((profile) => set({ profile: profile as UserProfile, loading: false }))
        .catch((err: Error) =>
          set({ profile: String(err?.message).includes('404') ? null : { id: userId, email: '' }, loading: false })
        );
    } catch {
      set({ hydrated: true, loading: false });
    }
  },

  setUser: async (user: UserProfile) => {
    await AsyncStorage.setItem(STORAGE_KEY, user.id);
    set({ userId: user.id, signedIn: true, profile: user });
  },

  refreshProfile: async () => {
    const { userId, profile } = get();
    try {
      const fresh = await api.getUser(userId);
      set({ profile: { ...(profile || {}), ...fresh } as UserProfile });
    } catch {
      /* keep last known profile */
    }
  },

  updateProfile: async (patch: Record<string, any>) => {
    const { userId, profile } = get();
    const updated = await api.updateUser(userId, patch);
    set({ profile: { ...(profile || {}), ...updated } as UserProfile });
  },

  // Signing out also removes the health data cached on the device, which may be shared.
  clearUser: async () => {
    const refresh = getRefreshToken();
    if (refresh) {
      // Ends the session on the server too; a copy of the token left on a backup stops working.
      fetch(`${API_V1}/auth/logout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refresh }),
      }).catch(() => {});
    }
    await setTokens(null);
    cache.clear();
    try {
      const keys = await AsyncStorage.getAllKeys();
      await AsyncStorage.multiRemove(keys.filter((k) => k === STORAGE_KEY || k.startsWith('adapfit:cache:')));
      await deleteLocalDatabase();
    } catch {
      /* nothing stored yet */
    }
    set({ userId: '', signedIn: false, profile: null });
  },
}));