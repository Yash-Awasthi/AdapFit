import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from '../services/api';

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
    try {
      const stored = await AsyncStorage.getItem(STORAGE_KEY);
      const userId = stored || 'default';
      set({ userId, hydrated: true });
      // Best-effort profile fetch; never block render on it.
      api
        .getUser(userId)
        .then((profile) => set({ profile: profile as UserProfile, loading: false }))
        .catch(() => set({ loading: false }));
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
    set({ userId: 'default', profile: null });
  },
}));