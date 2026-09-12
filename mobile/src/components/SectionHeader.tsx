import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useTheme } from '../services/theme';
import { spacing } from '../theme';

interface Props {
  title: string;
  action?: string;
  onAction?: () => void;
  /** Icon element to render before the title */
  icon?: React.ReactNode;
}

export function SectionHeader({ title, action, onAction, icon }: Props) {
  const { theme } = useTheme();
  return (
    <View style={styles.container}>
      <View style={styles.titleRow}>
        {icon}
        <Text style={[styles.title, { color: theme.text }]}>{title}</Text>
      </View>
      {action && (
        <Text style={[styles.action, { color: theme.primary }]} onPress={onAction}>
          {action}
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
    marginTop: spacing.sm,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
  },
  action: {
    fontSize: 14,
    fontWeight: '600',
  },
});
