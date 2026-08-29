/**
 * Floating back control for screens that draw their own header.
 *
 * The navigator header is transparent and those screens paint a title in the
 * same top-left corner, so the control needs its own scrim to stay readable
 * over a gradient, and the screen header needs BACK_BUTTON_INSET of left
 * padding to keep its title clear of it.
 */
import React from 'react';
import { TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

/** Left padding a screen-owned header needs so its title clears the control. */
export const BACK_BUTTON_INSET = 44;

export function BackButton({ fallback = '/menu' }: { fallback?: string }) {
  const router = useRouter();

  const goBack = () => {
    // Inside the tab navigator there is often no history to pop, and an
    // unguarded back() drops the user on the first tab rather than where
    // they came from.
    if (router.canGoBack()) router.back();
    else router.replace(fallback as any);
  };

  return (
    <TouchableOpacity
      onPress={goBack}
      hitSlop={12}
      style={styles.button}
      accessibilityRole="button"
      accessibilityLabel="Go back"
    >
      <Ionicons name="chevron-back" size={22} color="#FFFFFF" />
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    width: 34,
    height: 34,
    borderRadius: 17,
    marginLeft: 4,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.35)',
  },
});
