import React from 'react';
import { Text, StyleSheet, ActivityIndicator, Platform } from 'react-native';
import Animated, { useSharedValue, useAnimatedStyle, withSpring } from 'react-native-reanimated';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import * as Haptics from 'expo-haptics';
import { useDevSettings } from '../services/devSettings';
import { useTheme } from '../services/theme';
import { colors, radius, spacing } from '../theme';

interface Props {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  accessibilityLabel?: string;
  accessibilityHint?: string;
}

export function Button({
  title,
  onPress,
  variant = 'primary',
  size = 'md',
  loading,
  disabled,
  accessibilityLabel,
  accessibilityHint,
}: Props) {
  const { reduceMotion } = useDevSettings();
  const { theme } = useTheme();
  const scale = useSharedValue(1);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const tapGesture = Gesture.Tap()
    .onBegin(() => {
      if (!reduceMotion) scale.value = withSpring(0.96, { damping: 15, stiffness: 300 });
    })
    .onFinalize(() => {
      if (!reduceMotion) scale.value = withSpring(1, { damping: 15, stiffness: 300 });
    })
    .onEnd(() => {
      if (!disabled && !loading) {
        Haptics.selectionAsync();
        onPress();
      }
    });

  const variantStyles = {
    primary: {
      container: { backgroundColor: theme.primary },
      text: { color: '#fff' },
    },
    secondary: {
      container: { backgroundColor: theme.surface, borderWidth: 1, borderColor: theme.border },
      text: { color: theme.text },
    },
    ghost: {
      container: { backgroundColor: 'transparent' },
      text: { color: theme.primaryLight },
    },
    danger: {
      container: { backgroundColor: theme.danger },
      text: { color: '#fff' },
    },
  }[variant];

  const sizeStyles = {
    sm: { paddingVertical: 8, paddingHorizontal: 16 },
    md: { paddingVertical: 14, paddingHorizontal: 24 },
    lg: { paddingVertical: 18, paddingHorizontal: 32 },
  }[size];

  return (
    <GestureDetector gesture={tapGesture}>
      <Animated.View
        style={[
          styles.button,
          sizeStyles,
          variantStyles.container,
          disabled && styles.disabled,
          animatedStyle,
        ]}
      >
        {loading ? (
          <ActivityIndicator color={variant === 'primary' || variant === 'danger' ? '#fff' : theme.primaryLight} />
        ) : (
          <Text style={[styles.text, variantStyles.text]}>{title}</Text>
        )}
      </Animated.View>
    </GestureDetector>
  );
}

const styles = StyleSheet.create({
  button: {
    borderRadius: radius.button,
    alignItems: 'center',
    justifyContent: 'center',
  },
  disabled: {
    opacity: 0.5,
  },
  text: {
    fontSize: 16,
    fontWeight: '600',
  },
});
