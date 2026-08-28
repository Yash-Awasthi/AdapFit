import axios from 'axios';
import { API_V1 } from './config';

export const apiClient = axios.create({
  baseURL: API_V1,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

export interface RecoveryCalculationPayload {
  user_id: string;
  log_date: string;
  wearable_data?: {
    sleep_duration_hours?: number;
    sleep_efficiency_pct?: number;
    hrv_rmssd?: number;
    resting_heart_rate?: number;
  };
  subjective_checkin?: {
    soreness: number;
    fatigue: number;
    stress: number;
    sore_muscle_groups: string[];
  };
}

export const fetchRecoveryScore = async (payload: RecoveryCalculationPayload) => {
  const res = await apiClient.post('/recovery/calculate', payload);
  return res.data;
};

export const generateWorkoutRoutine = async (userId: string, targetDate: string, duration: number = 45) => {
  const res = await apiClient.post('/workouts/generate', {
    user_id: userId,
    target_date: targetDate,
    target_duration_minutes: duration,
  });
  return res.data;
};

export const completeWorkoutSession = async (payload: any) => {
  const res = await apiClient.post('/workouts/complete', payload);
  return res.data;
};

export const fetchACWRStatus = async (userId: string) => {
  const res = await apiClient.get(`/trends/acwr?user_id=${userId}`);
  return res.data;
};
