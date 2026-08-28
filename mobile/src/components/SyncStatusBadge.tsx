/**
 * Subtle sync status indicator: Synced / Syncing / Offline / Sync Error.
 */

import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { getSyncState, onSyncStateChange, type SyncState } from '../services/sync';
import { useTheme } from '../services/theme';

export function SyncStatusBadge() {
  const { theme } = useTheme();
  const [state, setState] = useState<SyncState>(getSyncState());

  useEffect(() => {
    return onSyncStateChange(setState);
  }, []);

  const color = {
    synced: theme.success,
    syncing: theme.warning,
    offline: theme.textMuted,
    error: theme.danger,
  }[state.status];

  const label = {
    synced: 'Synced',
    syncing: state.pendingCount > 0 ? `Syncing (${state.pendingCount})` : 'Syncing...',
    offline: 'Offline',
    error: 'Sync Error',
  }[state.status];

  const s = makeStyles(theme);

  return (
    <View style={s.container}>
      <View style={[s.dot, { backgroundColor: color }]} />
      <Text style={[s.label, { color }]}>{label}</Text>
    </View>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 4,
      paddingHorizontal: 8,
      paddingVertical: 4,
      borderRadius: 12,
      backgroundColor: theme.surface,
    },
    dot: {
      width: 6,
      height: 6,
      borderRadius: 3,
    },
    label: {
      fontSize: 11,
      fontWeight: '500',
    },
  });
}
