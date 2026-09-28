/**
 * Takes a photo of a skin spot and sends it for measurement. The server
 * measures and discards it; nothing is saved on the device either.
 */
import * as ImagePicker from 'expo-image-picker';
import { postForm } from './http';

// 2019-series coin diameters; older coins differ (the old ₹1 is 25 mm).
export const COINS = [
  { label: 'No coin', mm: null },
  { label: '₹1', mm: 20 },
  { label: '₹2', mm: 23 },
  { label: '₹5', mm: 25 },
  { label: '₹10', mm: 27 },
] as const;

export async function photographAndMeasure<T>(path: string, referenceMm: number | null, extra: Record<string, string> = {}): Promise<T | null | 'cancelled'> {
  const perm = await ImagePicker.requestCameraPermissionsAsync();
  const shot = perm.granted
    ? await ImagePicker.launchCameraAsync({ mediaTypes: ['images'], quality: 0.9 })
    : await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], quality: 0.9 });
  if (shot.canceled || !shot.assets?.[0]) return 'cancelled';
  const form = new FormData();
  form.append('file', { uri: shot.assets[0].uri, name: 'spot.jpg', type: 'image/jpeg' } as any);
  if (referenceMm) form.append('reference_mm', String(referenceMm));
  for (const [k, v] of Object.entries(extra)) form.append(k, v);
  return postForm<T>(path, form);
}
