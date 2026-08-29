/**
 * Devices — Wearable sync, connected devices, and data management
 */
import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, radius, presets } from '../../src/theme';

import { API_V1 as API } from '../../src/services/config';
const api = async (p: string, o?: RequestInit) => { try { const r = await fetch(`${API}${p}`, { headers: { 'Content-Type': 'application/json' }, ...o }); return r.ok ? await r.json() : null; } catch { return null; } };

const PLATFORMS = [
  { id: 'apple_health', name: 'Apple Health', icon: 'heart', color: '#FF2D55' },
  { id: 'google_fit', name: 'Google Fit', icon: 'walk', color: '#4285F4' },
  { id: 'fitbit', name: 'Fitbit', icon: 'watch', color: '#00B0B9' },
  { id: 'samsung_health', name: 'Samsung Health', icon: 'phone-portrait', color: '#1428A0' },
] as const;

export default function DevicesScreen() {
  const [devices, setDevices] = useState<any[]>([]);
  const [status, setStatus] = useState<any>({});
  const [syncHistory, setSyncHistory] = useState<any[]>([]);

  const load = useCallback(async () => {
    const [d, s, h] = await Promise.allSettled([api('/device-sync/devices'), api('/device-sync/status'), api('/device-sync/history')]);
    if (d.status === 'fulfilled') setDevices(d.value?.devices || []);
    if (s.status === 'fulfilled') setStatus(s.value || {});
    if (h.status === 'fulfilled') setSyncHistory(h.value?.history || []);
  }, []);

  useEffect(() => { load(); }, [load]);

  const connect = async (platform: string, name: string) => {
    const r = await api('/device-sync/connect', { method: 'POST', body: JSON.stringify({ platform, display_name: name }) });
    if (r?.connected) { Alert.alert('Connected!', `${name} is now connected`); load(); }
  };

  const sync = async (deviceId: string) => {
    const r = await api(`/device-sync/sync/${deviceId}`, { method: 'POST', body: '{}' });
    if (r?.synced) { Alert.alert('Synced!', `${r.records_synced} records synced`); load(); }
  };

  const disconnect = async (deviceId: string) => {
    Alert.alert('Disconnect', 'Remove this device?', [
      { text: 'Disconnect', style: 'destructive', onPress: async () => { await api(`/device-sync/disconnect/${deviceId}`, { method: 'DELETE' }); load(); } },
      { text: 'Cancel', style: 'cancel' },
    ]);
  };

  return (
    <ScrollView style={ds.container}>
      <View style={ds.header}>
        <Text style={typography.heading.h1}>Devices</Text>
        <Text style={typography.body.sm}>Connect wearables and health platforms</Text>
      </View>

      {/* Sync Status */}
      <View style={[presets.card, { marginHorizontal: spacing.lg }]}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text style={typography.heading.h4}>Sync Status</Text>
          <Text style={[typography.body.sm, { color: colors.health.calm }]}>{status.connected_devices || 0} devices</Text>
        </View>
        <Text style={[typography.body.xs, { marginTop: spacing.xs }]}>{status.total_synced_records || 0} total records synced</Text>
      </View>

      {/* Available Platforms */}
      <View style={[presets.card, { marginHorizontal: spacing.lg }]}>
        <Text style={[typography.heading.h4, { marginBottom: spacing.md }]}>Available Platforms</Text>
        {PLATFORMS.map(p => {
          const connected = devices.some((d: any) => d.platform === p.id);
          return (
            <TouchableOpacity key={p.id} style={ds.platformCard} onPress={() => !connected && connect(p.id, p.name)}>
              <Ionicons name={p.icon} size={24} color={p.color} />
              <View style={{ flex: 1 }}>
                <Text style={typography.label.lg}>{p.name}</Text>
                <Text style={[typography.body.xs, { color: connected ? colors.health.calm : colors.text.muted }]}>
                  {connected ? '✓ Connected' : 'Tap to connect'}
                </Text>
              </View>
              {connected && <Ionicons name="checkmark-circle" size={22} color={colors.health.calm} />}
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Connected Devices */}
      {devices.length > 0 && (
        <View style={[presets.card, { marginHorizontal: spacing.lg }]}>
          <Text style={[typography.heading.h4, { marginBottom: spacing.md }]}>Connected Devices</Text>
          {devices.map((d, i) => (
            <View key={i} style={ds.deviceCard}>
              <View style={{ flex: 1 }}>
                <Text style={typography.label.lg}>{d.name}</Text>
                <Text style={typography.body.xs}>Last sync: {d.last_sync} • {d.data_types?.length || 0} data types</Text>
              </View>
              <TouchableOpacity style={ds.syncBtn} onPress={() => sync(d.id)}><Ionicons name="sync" size={16} color={colors.primary} /></TouchableOpacity>
              <TouchableOpacity onPress={() => disconnect(d.id)}><Ionicons name="close-circle" size={20} color={colors.health.danger} /></TouchableOpacity>
            </View>
          ))}
        </View>
      )}

      {/* Sync History */}
      {syncHistory.length > 0 && (
        <View style={[presets.card, { marginHorizontal: spacing.lg }]}>
          <Text style={[typography.heading.h4, { marginBottom: spacing.md }]}>Sync History</Text>
          {syncHistory.slice(0, 5).map((h, i) => (
            <View key={i} style={ds.historyItem}>
              <Text style={typography.body.sm}>{h.device}</Text>
              <Text style={typography.body.xs}>{h.time} • {h.records} records • {h.status}</Text>
            </View>
          ))}
        </View>
      )}
      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const ds = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.primary },
  header: { padding: spacing.screenPadding, paddingTop: 50, paddingBottom: spacing.lg },
  platformCard: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, backgroundColor: colors.bg.input, padding: spacing.md, borderRadius: radius.md, marginBottom: spacing.sm, borderWidth: 1, borderColor: colors.surface.border },
  deviceCard: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, backgroundColor: colors.bg.input, padding: spacing.md, borderRadius: radius.md, marginBottom: spacing.sm, borderWidth: 1, borderColor: colors.surface.border },
  syncBtn: { width: 36, height: 36, borderRadius: 18, backgroundColor: colors.primaryMuted, justifyContent: 'center', alignItems: 'center' },
  historyItem: { paddingVertical: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.surface.divider },
});
