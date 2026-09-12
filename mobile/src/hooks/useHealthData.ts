/**
 * React Query hooks for health data.
 * Replaces raw fetch calls in home screen with cached, validated data.
 */
import { useQuery, useMutation } from '@tanstack/react-query';
import { assessStress, getWellbeingReport, logSleep } from '../services/api-client';

export function useStressAssessment(params?: {
  mood_score: number;
  energy_level: number;
  sleep_quality: number;
}) {
  return useQuery({
    queryKey: ['stress', params],
    queryFn: () => assessStress(params!),
    enabled: !!params, // DISABLED until real user data is available
  });
}

export function useWellbeingReport() {
  return useQuery({
    queryKey: ['wellbeing'],
    queryFn: getWellbeingReport,
  });
}

export function useLogSleep() {
  return useMutation({
    mutationFn: logSleep,
  });
}
