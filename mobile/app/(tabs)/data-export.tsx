/**
 * Data Export — download your records as CSV, or everything the app holds
 * about you as one JSON file. Files are fetched from the server and saved
 * where you choose.
 */
import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Alert, ActivityIndicator, Platform, Share } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import * as FileSystem from 'expo-file-system/legacy';
import { colors, spacing } from '../../src/theme';
import { GlassCard, SectionHeaderPremium } from '../../src/components/PremiumComponents';
import { useApi } from '../../src/hooks/useApi';
import { asArray } from '../../src/services/http';
import { API_V1 } from '../../src/services/config';
import { authedFetch } from '../../src/services/authToken';

const TINT = '#22C55E';

interface DataType { id: string; name: string; description: string }

async function saveFile(name: string, mime: string, contents: string) {
  if (Platform.OS === 'android') {
    const saf = FileSystem.StorageAccessFramework;
    const perm = await saf.requestDirectoryPermissionsAsync();
    if (!perm.granted) return false;
    const uri = await saf.createFileAsync(perm.directoryUri, name, mime);
    await FileSystem.writeAsStringAsync(uri, contents);
    return true;
  }
  const uri = `${FileSystem.documentDirectory}${name}`;
  await FileSystem.writeAsStringAsync(uri, contents);
  await Share.share({ url: uri, title: name });
  return true;
}

export default function DataExportScreen() {
  const { data } = useApi<{ data_types: DataType[] }>('/export/formats');
  const [busy, setBusy] = useState<string | null>(null);
  const types = asArray<DataType>(data?.data_types);

  const download = async (id: string) => {
    setBusy(id);
    try {
      const all = id === 'all';
      const res = await authedFetch(`${API_V1}/export/${id}${all ? '' : '?format=csv'}`);
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const text = await res.text();
      const date = new Date().toISOString().slice(0, 10);
      const saved = await saveFile(`adapfit-${id}-${date}.${all ? 'json' : 'csv'}`, all ? 'application/json' : 'text/csv', text);
      if (saved) Alert.alert('Saved', all ? 'Your complete data file is saved.' : 'The CSV file is saved.');
    } catch (e: any) {
      Alert.alert('Export failed', e?.message ?? String(e));
    }
    setBusy(null);
  };

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <LinearGradient colors={[TINT, '#15803D', colors.bg.deep]} style={styles.hero}>
          <Text style={styles.heroMuted}>Your Data</Text>
          <Text style={styles.heroTitle}>Take a copy anytime</Text>
          <Text style={styles.heroBody}>It is your data. Download it as spreadsheets, or everything in one file.</Text>
        </LinearGradient>

        <View style={styles.section}>
          <SectionHeaderPremium title="Everything" icon="archive" iconColor={TINT} />
          {types.filter((t) => t.id === 'all').map((t) => (
            <TouchableOpacity key={t.id} onPress={() => download(t.id)} disabled={!!busy}>
              <GlassCard style={styles.row}>
                <Ionicons name="cloud-download" size={24} color={TINT} />
                <View style={{ flex: 1 }}>
                  <Text style={styles.rowTitle}>{t.name} (JSON)</Text>
                  <Text style={styles.rowDesc}>{t.description}</Text>
                </View>
                {busy === t.id ? <ActivityIndicator color={TINT} /> : <Ionicons name="chevron-forward" size={18} color={colors.text.muted} />}
              </GlassCard>
            </TouchableOpacity>
          ))}
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Spreadsheets (CSV)" icon="grid" iconColor={TINT} />
          {types.filter((t) => t.id !== 'all').map((t) => (
            <TouchableOpacity key={t.id} onPress={() => download(t.id)} disabled={!!busy}>
              <GlassCard style={[styles.row, styles.gap]}>
                <Ionicons name="document-text" size={22} color={TINT} />
                <View style={{ flex: 1 }}>
                  <Text style={styles.rowTitle}>{t.name}</Text>
                  <Text style={styles.rowDesc}>{t.description}</Text>
                </View>
                {busy === t.id ? <ActivityIndicator color={TINT} /> : <Ionicons name="download-outline" size={18} color={colors.text.muted} />}
              </GlassCard>
            </TouchableOpacity>
          ))}
          {types.length === 0 && <Text style={styles.rowDesc}>Could not reach the server.</Text>}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  scrollContent: { paddingBottom: 100 },
  hero: { paddingTop: 60, paddingBottom: 24, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 24, borderBottomRightRadius: 24 },
  heroMuted: { color: 'rgba(255,255,255,0.8)', fontSize: 13 },
  heroTitle: { color: '#fff', fontSize: 26, fontWeight: '800', marginTop: 6 },
  heroBody: { color: 'rgba(255,255,255,0.9)', fontSize: 14, marginTop: 6, lineHeight: 20 },
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  row: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  gap: { marginBottom: 10 },
  rowTitle: { color: colors.text.primary, fontSize: 15, fontWeight: '700' },
  rowDesc: { color: colors.text.muted, fontSize: 12, marginTop: 2 },
});
