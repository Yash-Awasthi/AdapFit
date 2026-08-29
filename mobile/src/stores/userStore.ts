import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from '../services/api';
import { restoreToken, setToken } from '../services/authToken';

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
  /** Persisted user id (falls back to the seeded 'default' user). */
  userId: string;
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
  userId: 'default',
  profile: null,
  hydrated: false,
  loading: true,

  hydrate: async () => {
    // Must land before the profile fetch below, which needs the header.
    await restoreToken();
    try {
      const stored = await AsyncStorage.getItem(STORAGE_KEY);
      const userId = stored || 'default';
      set({ userId, hydrated: true });
      // Best-effort profile fetch; never block render on it. Falling back to
      // the seeded identity keeps a reachable backend out of the onboarding
      // trap, which the root layout otherwise enforces whenever profile is null.
      api
        .getUser(userId)
        .then((profile) => set({ profile: profile as UserProfile, loading: false }))
        .catch(() =>
          api
            .getUser('default')
            .then((profile) => set({ userId: 'default', profile: profile as UserProfile, loading: false }))
            .catch(() => set({ loading: false }))
        );
    } catch {
      set({ hydrated: true, loading: false });
    }
  },

  setUser: async (user: UserProfile) => {
    await AsyncStorage.setItem(STORAGE_KEY, user.id);
    set({ userId: user.id, profile: user });
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

  clearUser: async () => {
    await AsyncStorage.removeItem(STORAGE_KEY);
    await setToken(null);
    set({ userId: 'default', profile: null });
  },
}));