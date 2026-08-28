import React from 'react';
import { Text, StyleSheet, ActivityIndicator, Pressable } from 'react-native';
import Animated, { useSharedValue, useAnimatedStyle, withSpring } from 'react-native-reanimated';
import * as Haptics from 'expo-haptics';
import { useDevSettings } from '../services/devSettings';

interface Props {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'ghost';
  loading?: boolean;
  disabled?: boolean;
  accessibilityLabel?: string;
  accessibilityHint?: string;
}

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

export function Button({ title, onPress, variant = 'primary', loading, disabled, accessibilityLabel, accessibilityHint }: Props) {
  const { reduceMotion } = useDevSettings();
  const scale = useSharedValue(1);
  const animatedStyle = useAnimatedStyle(() => ({ transform: [{ scale: scale.value }] }));

  return (
    <AnimatedPressable
      style={[styles.button, styles[variant as keyof typeof styles], disabled && styles.disabled, animatedStyle]}
      onPressIn={() => { if (!reduceMotion) scale.value = withSpring(0.96, { damping: 15, stiffness: 300 }); }}
      onPressOut={() => { if (!reduceMotion) scale.value = withSpring(1, { damping: 15, stiffness: 300 }); }}
      onPress={() => { if (!disabled && !loading) { Haptics.selectionAsync(); onPress(); } }}
      disabled={disabled || loading}
      accessibilityLabel={accessibilityLabel}
      accessibilityHint={accessibilityHint}
      accessibilityRole="button"
    >
      {loading ? (
        <ActivityIndicator color={variant === 'primary' ? '#fff' : '#818CF8'} />
      ) : (
        <Text style={[styles.text, styles[(variant + 'Text') as keyof typeof styles]]}>{title}</Text>
      )}
    </AnimatedPressable>
  );
}

const styles = StyleSheet.create({
  button: {
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primary: {
    backgroundColor: '#6366F1',
  },
  secondary: {
    backgroundColor: '#1E293B',
  },
  ghost: {
    backgroundColor: 'transparent',
  },
  disabled: {
    opacity: 0.5,
  },
  text: {
    fontSize: 16,
    fontWeight: '600',
  },
  primaryText: {
    color: '#fff',
  },
  secondaryText: {
    color: '#F8FAFC',
  },
  ghostText: {
    color: '#818CF8',
  },
});
