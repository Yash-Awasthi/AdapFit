import { create } from 'zustand';
import { API_BASE_URL } from '../services/config';

const API = API_BASE_URL;

interface RecoveryData {
  recovery_score: number;
  readiness_state: 'OPTIMAL' | 'MODERATE' | 'REDUCED' | 'DEPLETED';
  metrics_breakdown: {
    hrv_z_score: number | null;
    sleep_score: number;
    subjective_score: number;
    acwr: number | null;
  };
  recommendation_directive: string;
}

interface RecoveryStore {
  data: RecoveryData | null;
  loading: boolean;
  error: string | null;
  fetchRecovery: (userId: string) => Promise<void>;
  clear: () => void;
}

export const useRecoveryStore = create<RecoveryStore>((set) => ({
  data: null,
  loading: false,
  error: null,

  fetchRecovery: async (userId: string) => {
    set({ loading: true, error: null });
    try {
      const res = await fetch(`${API}/api/v1/recovery-logs?user_id=${userId}&days=1`);
      if (res.ok) {
        const json = await res.json();
        if (json.items?.length > 0) {
          set({ data: json.items[json.items.length - 1], loading: false });
          return;
        }
      }
      set({ data: null, loading: false });
    } catch (e) {
      set({ error: 'Failed to fetch recovery data', loading: false });
    }
  },

  clear: () => set({ data: null, loading: false, error: null }),
}));
