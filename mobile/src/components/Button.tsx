import React from 'react';
import { Text, StyleSheet, ActivityIndicator, Pressable } from 'react-native';
import Animated, { useSharedValue, useAnimatedStyle, withSpring } from 'react-native-reanimated';
import * as Haptics from 'expo-haptics';
import { useDevSettings } from '../services/devSettings';
import { useTheme } from '../services/theme';

interface Props {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'ghost';
  loading?: boolean;
  disabled?: boolean;
  accessibilityLabel?: string;
  accessibilityHint?: string;
}

export function Button({ title, onPress, variant = 'primary', loading, disabled, accessibilityLabel, accessibilityHint }: Props) {
  const { reduceMotion } = useDevSettings();
  const { theme } = useTheme();
  const scale = useSharedValue(1);
  const animatedStyle = useAnimatedStyle(() => ({ transform: [{ scale: scale.value }] }));

  const variantColorStyle =
    variant === 'primary'
      ? { backgroundColor: theme.primary }
      : variant === 'secondary'
      ? { backgroundColor: theme.surface }
      : null;
  const textColorStyle =
    variant === 'primary' ? { color: '#fff' } : variant === 'secondary' ? { color: theme.text } : { color: theme.primaryLight };

  return (
    <Pressable
      onPressIn={() => { if (!reduceMotion) scale.value = withSpring(0.96, { damping: 15, stiffness: 300 }); }}
      onPressOut={() => { if (!reduceMotion) scale.value = withSpring(1, { damping: 15, stiffness: 300 }); }}
      onPress={() => { if (!disabled && !loading) { Haptics.selectionAsync(); onPress(); } }}
      disabled={disabled || loading}
      accessibilityLabel={accessibilityLabel}
      accessibilityHint={accessibilityHint}
      accessibilityRole="button"
    >
      <Animated.View
        style={[styles.button, variant === 'ghost' && styles.ghost, variantColorStyle, disabled && styles.disabled, animatedStyle]}
      >
        {loading ? (
          <ActivityIndicator color={variant === 'primary' ? '#fff' : theme.primaryLight} />
        ) : (
          <Text style={[styles.text, textColorStyle]}>{title}</Text>
        )}
      </Animated.View>
    </Pressable>
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
});
