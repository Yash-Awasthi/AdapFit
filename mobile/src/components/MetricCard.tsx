import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useTheme, CARD_SHADOW } from '../services/theme';
import { colors, spacing, radius } from '../theme';

interface Props {
  label: string;
  value: string | number;
  color?: string;
  variant?: 'default' | 'compact' | 'highlight';
}

export function MetricCard({ label, value, color, variant = 'default' }: Props) {
  const { theme } = useTheme();

  const variantStyles = {
    default: { padding: 16, borderRadius: 14 },
    compact: { padding: 12, borderRadius: 12 },
    highlight: { padding: 16, borderRadius: 14, borderWidth: 2, borderColor: (color || theme.primary) + '40' },
  }[variant];

  return (
    <View style={[styles.card, CARD_SHADOW, { backgroundColor: theme.surface, borderColor: theme.border }, variantStyles]}>
      <Text
        style={[styles.value, { color: color || theme.text }]}
        numberOfLines={1}
        adjustsFontSizeToFit
        minimumFontScale={0.6}
      >
        {value}
      </Text>
      <Text style={[styles.label, { color: theme.textMuted }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    width: '48%',
    borderWidth: 1,
  },
  value: {
    fontSize: 24,
    fontWeight: '700',
  },
  label: {
    fontSize: 12,
    marginTop: 4,
  },
});
