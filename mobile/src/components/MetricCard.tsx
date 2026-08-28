import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useTheme, CARD_SHADOW } from '../services/theme';

interface Props {
  label: string;
  value: string | number;
  color?: string;
}

export function MetricCard({ label, value, color }: Props) {
  const { theme } = useTheme();
  return (
    <View style={[styles.card, CARD_SHADOW, { backgroundColor: theme.surface, borderColor: theme.border }]}>
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
    borderRadius: 14,
    borderWidth: 1,
    padding: 16,
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
