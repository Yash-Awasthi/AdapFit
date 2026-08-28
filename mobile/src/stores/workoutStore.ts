import { create } from 'zustand';
import { api } from '../services/api';

interface Workout {
  workout_id: string;
  title: string;
  exercises: {
    exercise_id: string;
    name: string;
    target_muscle: string;
    sets: number;
    target_reps: string;
    gif_url?: string;
  }[];
  adaptation_rationale: string;
}

interface WorkoutStore {
  workouts: Workout[];
  loading: boolean;
  generating: boolean;
  error: string | null;
  fetchWorkouts: (userId: string) => Promise<void>;
  generateWorkout: (userId: string, duration?: number) => Promise<Workout | null>;
  clear: () => void;
}

export const useWorkoutStore = create<WorkoutStore>((set, get) => ({
  workouts: [],
  loading: false,
  generating: false,
  error: null,

  fetchWorkouts: async (userId: string) => {
    set({ loading: true, error: null });
    try {
      const res = await api.getWorkouts(userId, 7);
      set({ workouts: res.items || [], loading: false });
    } catch (e) {
      set({ error: 'Failed to fetch workouts', loading: false });
    }
  },

  generateWorkout: async (userId: string, duration = 45) => {
    set({ generating: true, error: null });
    try {
      const workout = await api.generateWorkout({
        user_id: userId,
        target_date: new Date().toISOString().split('T')[0],
        target_duration_minutes: duration,
      });
      set((state) => ({
        workouts: [workout, ...state.workouts],
        generating: false,
      }));
      return workout;
    } catch (e) {
      set({ error: 'Failed to generate workout', generating: false });
      return null;
    }
  },

  clear: () => set({ workouts: [], loading: false, generating: false, error: null }),
}));
