/**
 * TRACK 8: Subtle sync status indicator for the app header.
 * Shows: Synced / Syncing / Offline Mode
 */

import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { getSyncState, onSyncStateChange, type SyncState } from '../services/sync';

export function SyncStatusBadge() {
  const [state, setState] = useState<SyncState>(getSyncState());

  useEffect(() => {
    return onSyncStateChange(setState);
  }, []);

  const color = {
    synced: '#22C55E',
    syncing: '#F59E0B',
    offline: '#94A3B8',
    error: '#EF4444',
  }[state.status];

  const label = {
    synced: 'Synced',
    syncing: state.pendingCount > 0 ? `Syncing (${state.pendingCount})` : 'Syncing...',
    offline: 'Offline',
    error: 'Sync Error',
  }[state.status];

  return (
    <View style={styles.container}>
      <View style={[styles.dot, { backgroundColor: color }]} />
      <Text style={[styles.label, { color }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    backgroundColor: '#1E293B',
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
