import { useUserStore } from '../stores';

export const GENDER_OPTIONS = [
  { value: 'female', label: 'Female' },
  { value: 'male', label: 'Male' },
  { value: 'other', label: 'Other' },
  { value: 'prefer_not_to_say', label: 'Prefer not to say' },
] as const;

/**
 * Whether to surface cycle, fertility, and pregnancy features.
 *
 * Returns false until the profile has hydrated, so these entries fade in once
 * rather than appearing and then vanishing on a slow profile fetch.
 */
export function useFemaleFeatures(): boolean {
  const hydrated = useUserStore((s) => s.hydrated);
  const gender = useUserStore((s) => s.profile?.gender);
  return hydrated && gender === 'female';
}
