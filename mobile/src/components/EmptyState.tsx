import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useTheme } from '../services/theme';

interface Props {
  title: string;
  message: string;
}

export function EmptyState({ title, message }: Props) {
  const { theme } = useTheme();
  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      <Text style={[styles.title, { color: theme.text }]}>{title}</Text>
      <Text style={[styles.message, { color: theme.textMuted }]}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
  },
  message: {
    fontSize: 14,
    textAlign: 'center',
  },
});
