/**
 * Medication Tracker — today's schedule, adherence and refill alerts.
 *
 * Marking a dose writes it and reloads rather than flipping a local flag: the
 * adherence figure above the list is computed server-side from the same logs,
 * so an optimistic tick would disagree with the score next to it.
 */
import React, { useCallback, useEffect, useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  ActivityIndicator, RefreshControl, Alert, Modal, TextInput, AppState, Linking, Platform,
} from 'react-native';
import { applyReminders } from '../../src/services/reminders';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { colors, spacing, radius } from '../../src/theme';
import { GlassCard, SectionHeaderPremium, ScoreRing, ProgressBarPremium } from '../../src/components/PremiumComponents';
import { SCREEN_HEADER_TOP } from '../../src/theme/layout';
import { useApis } from '../../src/hooks/useApi';
import { getJson, postJson, asArray } from '../../src/services/http';

interface ScheduleEntry {
  medication: string;
  dosage: string;
  time: string;
  status: 'taken' | 'pending' | 'missed' | 'skipped';
  category: string;
  med_id: string;
}

interface TodaySchedule {
  date: string;
  total_doses: number;
  taken: number;
  pending: number;
  missed: number;
  adherence_pct: number;
  schedule: ScheduleEntry[];
}

interface RefillAlert {
  medication: string;
  refill_date: string;
  days_until: number;
  urgency: 'critical' | 'warning';
}

// Colour is per category rather than per medication: a stable palette keyed by
// list position would recolour every row as soon as one is added.
const CATEGORY_COLOR: Record<string, string> = {
  prescription: '#EF4444',
  supplement: '#F59E0B',
  otc: '#3B82F6',
};

function colorFor(category: string): string {
  return CATEGORY_COLOR[category] ?? '#8B5CF6';
}

function AddMedicationModal({ visible, onClose, onAdded }: {
  visible: boolean; onClose: () => void; onAdded: () => void;
}) {
  const [name, setName] = useState('');
  const [dosage, setDosage] = useState('');
  const [time, setTime] = useState('08:00');
  const [saving, setSaving] = useState(false);
  const [suggestions, setSuggestions] = useState<IndianProduct[]>([]);

  useEffect(() => {
    const q = name.trim();
    if (q.length < 3) { setSuggestions([]); return; }
    const timer = setTimeout(async () => {
      const r = await getJson<{ products: IndianProduct[] }>(`/medication/india-search?q=${encodeURIComponent(q)}`);
      setSuggestions(asArray<IndianProduct>(r?.products).filter((p) => p.brand !== q).slice(0, 5));
    }, 300);
    return () => clearTimeout(timer);
  }, [name]);

  const save = async () => {
    if (!name.trim() || !dosage.trim()) {
      Alert.alert('Add medication', 'Name and dosage are both needed.');
      return;
    }
    setSaving(true);
    const result = await postJson('/medication/add', {
      name: name.trim(),
      dosage: dosage.trim(),
      frequency: 'once_daily',
      times: [time.trim()],
      category: 'supplement',
    });
    setSaving(false);
    if (!result) {
      Alert.alert('Could not save', 'The medication was not added. Check your connection and try again.');
      return;
    }
    setName('');
    setDosage('');
    onAdded();
    onClose();
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.modalBackdrop}>
        <View style={styles.modalCard}>
          <Text style={styles.modalTitle}>Add a medication</Text>
          <TextInput
            style={styles.input}
            placeholder="Name (e.g. Vitamin D3)"
            placeholderTextColor={colors.text.muted}
            value={name}
            onChangeText={setName}
            accessibilityLabel="Medication name"
          />
          {suggestions.map((p) => (
            <TouchableOpacity key={p.brand + p.pack} onPress={() => { setName(p.brand); setDosage(p.composition); setSuggestions([]); }}
              accessibilityRole="button" style={{ paddingVertical: 6 }}>
              <Text style={styles.medDetail}>{p.brand}</Text>
              <Text style={styles.emptyBody}>{p.composition} · {p.manufacturer}</Text>
            </TouchableOpacity>
          ))}
          <TextInput
            style={styles.input}
            placeholder="Dosage (e.g. 2000 IU)"
            placeholderTextColor={colors.text.muted}
            value={dosage}
            onChangeText={setDosage}
            accessibilityLabel="Dosage"
          />
          <TextInput
            style={styles.input}
            placeholder="Time (24h, e.g. 08:00)"
            placeholderTextColor={colors.text.muted}
            value={time}
            onChangeText={setTime}
            accessibilityLabel="Time of day"
          />
          <View style={styles.modalActions}>
            <TouchableOpacity onPress={onClose} style={[styles.modalButton, styles.modalCancel]}>
              <Text style={styles.modalCancelText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={save} disabled={saving} style={[styles.modalButton, styles.modalSave]}>
              <Text style={styles.modalSaveText}>{saving ? 'Saving…' : 'Add'}</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

interface IndianProduct { brand: string; manufacturer: string; pack: string; composition: string }
interface DrugInfo {
  india?: IndianProduct[];
  india_source?: string;
  searched_as: string;
  matches: { brand_name: string | null; generic_name: string | null; purpose: string[]; warnings: string[] }[];
  recalls: { reason: string; classification: string; date: string }[];
  source: string;
}
interface Interaction { drug_1: string; drug_2: string; severity: string; effect: string; next_step: string; for_your_doctor: string }

export default function MedicationScreen() {
  const [adding, setAdding] = useState(false);
  const [openInfo, setOpenInfo] = useState<string | null>(null);
  const [info, setInfo] = useState<Record<string, DrugInfo | 'loading' | 'error'>>({});
  const [interactions, setInteractions] = useState<Interaction[] | null>(null);

  const toggleInfo = useCallback(async (name: string) => {
    if (openInfo === name) return setOpenInfo(null);
    setOpenInfo(name);
    if (info[name] && info[name] !== 'error') return;
    setInfo((m) => ({ ...m, [name]: 'loading' }));
    const r = await getJson<DrugInfo>(`/medication/drug-info?name=${encodeURIComponent(name.replace(/[^A-Za-z0-9 -]/g, ' ').trim())}`);
    setInfo((m) => ({ ...m, [name]: r ?? 'error' }));
  }, [openInfo, info]);
  const { data, loading, refreshing, refresh, reload } = useApis<{
    today: TodaySchedule;
    refills: { alerts: RefillAlert[] };
  }>({ today: '/medication/today', refills: '/medication/refills' });

  const today = data.today ?? null;
  const schedule = asArray<ScheduleEntry>(today?.schedule);
  const refills = asArray<RefillAlert>(data.refills?.alerts);
  const refillByName = new Map(refills.map((r) => [r.medication, r]));

  const checkInteractions = useCallback(async () => {
    const names = Array.from(new Set(schedule.map((e) => e.medication)));
    const r = await postJson<{ data: { interactions: Interaction[]; resolved?: { message?: string }[] } }>('/drug-interactions/check', { medications: names });
    if (!r) return Alert.alert('Unavailable', 'The interaction check could not run.');
    setInteractions(asArray<Interaction>(r.data?.interactions));
    const unclear = asArray<{ message?: string }>(r.data?.resolved).map((x) => x.message).filter(Boolean);
    if (unclear.length) Alert.alert('Check the exact product', unclear.join('\n\n'));
  }, [schedule]);

  const markTaken = useCallback(async (entry: ScheduleEntry) => {
    if (entry.status === 'taken') return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    const result = await postJson('/medication/dose', { medication_id: entry.med_id, status: 'taken' });
    if (!result) {
      Alert.alert('Not recorded', 'The dose could not be logged. Try again when you are back online.');
      return;
    }
    await reload();
  }, [reload]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.contentContainer}
      showsVerticalScrollIndicator={false}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.primary} />}
    >
      <LinearGradient colors={['#F59E0B', '#F97316']} style={styles.header}>
        <Text style={styles.headerTitle} accessibilityRole="header">Medications</Text>
        <Text style={styles.headerSubtitle}>Track your medication schedule</Text>
      </LinearGradient>

      <View style={styles.scoreSection}>
        <ScoreRing
          score={today?.total_doses ? today.adherence_pct : null}
          size={120}
          strokeWidth={8}
          color={colors.health.calm}
          label="ADHERENCE"
        />
        <View style={styles.scoreInfo}>
          <Text style={styles.scoreValue}>{today?.taken ?? 0}/{today?.total_doses ?? 0}</Text>
          <Text style={styles.scoreLabel}>taken today</Text>
          <ProgressBarPremium
            value={today?.taken ?? 0}
            max={Math.max(1, today?.total_doses ?? 0)}
            color={colors.health.calm}
            height={6}
          />
        </View>
      </View>

      <SectionHeaderPremium icon="calendar" iconColor="#F59E0B" title="Today's Schedule" />

      {schedule.length > 0 && Platform.OS === 'android' && Number(Platform.Version) >= 31 && (
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityHint="Opens Android settings for alarms and reminders"
          onPress={() => {
            // Alarms already scheduled stay inexact; rebuild them when the user comes back from the setting.
            const sub = AppState.addEventListener('change', (state) => {
              if (state !== 'active') return;
              sub.remove();
              applyReminders(false);
            });
            Linking.sendIntent('android.settings.REQUEST_SCHEDULE_EXACT_ALARM').catch(() => Linking.openSettings());
          }}
        >
          <GlassCard variant="light" style={styles.medCard}>
            <Text style={styles.emptyTitle}>On-time dose reminders</Text>
            <Text style={styles.emptyBody}>
              Android may delay reminders by up to an hour. Turn on "Alarms & reminders" for AdapFit so each dose
              reminder rings at its time. Tap to open the setting.
            </Text>
          </GlassCard>
        </TouchableOpacity>
      )}

      {schedule.length === 0 && (
        <GlassCard variant="light" style={styles.medCard}>
          <Text style={styles.emptyTitle}>Nothing scheduled</Text>
          <Text style={styles.emptyBody}>
            Add a medication and its times, and the doses for each day appear here.
          </Text>
        </GlassCard>
      )}

      {schedule.map((entry) => {
        const tint = colorFor(entry.category);
        const refill = refillByName.get(entry.medication);
        return (
          <GlassCard key={`${entry.med_id}-${entry.time}`} variant="light" style={styles.medCard}>
            <View style={styles.medRow}>
              <View style={[styles.medIcon, { backgroundColor: tint + '15' }]}>
                <Ionicons name="medical" size={20} color={tint} />
              </View>
              <TouchableOpacity style={{ flex: 1 }} onPress={() => toggleInfo(entry.medication)}
                accessibilityLabel={`About ${entry.medication}`}>
                <Text style={styles.medName}>{entry.medication}</Text>
                <Text style={styles.medDetail}>{entry.dosage} • {entry.time} · tap for info</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.medCheck, entry.status === 'taken' && { backgroundColor: colors.health.calm }]}
                onPress={() => markTaken(entry)}
                accessibilityRole="button"
                accessibilityLabel={
                  entry.status === 'taken'
                    ? `${entry.medication} already taken`
                    : `Mark ${entry.medication} as taken`
                }
              >
                <Ionicons
                  name={entry.status === 'taken' ? 'checkmark' : 'add'}
                  size={18}
                  color={entry.status === 'taken' ? '#FFF' : colors.text.muted}
                />
              </TouchableOpacity>
            </View>
            {openInfo === entry.medication && (() => {
              const d = info[entry.medication];
              if (d === 'loading' || d === undefined) return <ActivityIndicator style={{ marginTop: 8 }} color={colors.primary} />;
              if (d === 'error') return <Text style={styles.medDetail}>Could not reach the drug database.</Text>;
              const m = d.matches[0];
              const india = asArray<IndianProduct>(d.india)[0];
              return (
                <View style={{ marginTop: 8 }}>
                  {india && <Text style={styles.medDetail}>In India: {india.brand} · {india.composition} · {india.manufacturer}</Text>}
                  {m ? (
                    <>
                      <Text style={styles.medDetail}>{[m.brand_name, m.generic_name].filter(Boolean).join(' · ')}</Text>
                      {m.purpose[0] ? <Text style={styles.emptyBody}>{m.purpose[0]}</Text> : null}
                      {m.warnings[0] ? <Text style={styles.emptyBody} numberOfLines={6}>{m.warnings[0]}</Text> : null}
                    </>
                  ) : (
                    <Text style={styles.emptyBody}>No US FDA label found for "{d.searched_as}". Try the generic name.</Text>
                  )}
                  {d.recalls.length > 0 && <Text style={[styles.refillText, { marginTop: 6 }]}>{d.recalls.length} FDA recall record(s) mention this name. Ask your pharmacist whether they apply to your pack.</Text>}
                  <Text style={[styles.medDetail, { marginTop: 6 }]}>{d.source}</Text>
                </View>
              );
            })()}
            {refill && (
              <View style={styles.refillWarning}>
                <Ionicons name="warning" size={12} color="#F59E0B" />
                <Text style={styles.refillText}>
                  {refill.days_until === 0 ? 'Refill due today' : `Refill in ${refill.days_until} days`}
                </Text>
              </View>
            )}
          </GlassCard>
        );
      })}

      {schedule.length > 1 && (
        <GlassCard variant="light" style={styles.medCard}>
          <TouchableOpacity onPress={checkInteractions} accessibilityRole="button">
            <Text style={styles.medName}>Check interactions between my medicines</Text>
          </TouchableOpacity>
          {interactions !== null && (interactions.length === 0 ? (
            <Text style={styles.emptyBody}>No known interactions between these medicines in our database. Your pharmacist can double-check.</Text>
          ) : interactions.map((it, i) => (
            <View key={i} style={{ marginTop: 10 }}>
              <Text style={[styles.medName, { color: it.severity === 'major' || it.severity === 'contraindicated' ? '#EF4444' : '#F59E0B' }]}>
                {it.drug_1} + {it.drug_2} ({it.severity})
              </Text>
              <Text style={styles.emptyBody}>{it.effect}</Text>
              <Text style={styles.emptyBody}>{it.next_step}</Text>
              <Text style={styles.medDetail}>For your doctor: {it.for_your_doctor}</Text>
            </View>
          )))}
        </GlassCard>
      )}

      <TouchableOpacity
        style={styles.addButton}
        onPress={() => setAdding(true)}
        accessibilityRole="button"
        accessibilityLabel="Add a medication"
      >
        <Ionicons name="add" size={18} color="#FFF" />
        <Text style={styles.addButtonText}>Add medication</Text>
      </TouchableOpacity>

      <AddMedicationModal visible={adding} onClose={() => setAdding(false)} onAdded={reload} />

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  contentContainer: { paddingBottom: 100 },
  center: { flex: 1, backgroundColor: colors.bg.deep, justifyContent: 'center', alignItems: 'center' },
  header: { paddingTop: SCREEN_HEADER_TOP, paddingBottom: spacing.xl, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 28, borderBottomRightRadius: 28 },
  headerTitle: { fontSize: 24, fontWeight: '800', color: '#FFF' },
  headerSubtitle: { fontSize: 14, color: 'rgba(255,255,255,0.7)', marginTop: 4 },

  scoreSection: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.xl, marginTop: spacing.xl, marginBottom: spacing.lg, paddingHorizontal: spacing.screenPadding },
  scoreInfo: { flex: 1 },
  scoreValue: { fontSize: 28, fontWeight: '800', color: colors.text.primary },
  scoreLabel: { fontSize: 13, color: colors.text.muted, marginBottom: spacing.sm },

  medCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  medRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  medIcon: { width: 40, height: 40, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  medName: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  medDetail: { fontSize: 12, color: colors.text.muted, marginTop: 2 },
  medCheck: { width: 36, height: 36, borderRadius: 18, backgroundColor: colors.surface.divider, justifyContent: 'center', alignItems: 'center' },
  refillWarning: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: spacing.sm, paddingHorizontal: spacing.md, paddingVertical: spacing.xs, backgroundColor: '#F59E0B15', borderRadius: 6 },
  refillText: { fontSize: 11, color: '#F59E0B', fontWeight: '600' },

  emptyTitle: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  emptyBody: { fontSize: 13, color: colors.text.muted, marginTop: 4, lineHeight: 18 },

  addButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.xs, marginHorizontal: spacing.screenPadding, marginTop: spacing.lg, paddingVertical: spacing.md, borderRadius: radius.lg, backgroundColor: '#F59E0B' },
  addButtonText: { fontSize: 15, fontWeight: '700', color: '#FFF' },

  modalBackdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', justifyContent: 'flex-end' },
  modalCard: { backgroundColor: colors.bg.elevated, padding: spacing.xl, borderTopLeftRadius: 24, borderTopRightRadius: 24, gap: spacing.md },
  modalTitle: { fontSize: 18, fontWeight: '800', color: colors.text.primary },
  input: { backgroundColor: colors.surface.divider, borderRadius: radius.md, paddingHorizontal: spacing.md, paddingVertical: spacing.md, color: colors.text.primary, fontSize: 15 },
  modalActions: { flexDirection: 'row', gap: spacing.md, marginTop: spacing.sm },
  modalButton: { flex: 1, paddingVertical: spacing.md, borderRadius: radius.md, alignItems: 'center' },
  modalCancel: { backgroundColor: colors.surface.divider },
  modalCancelText: { color: colors.text.muted, fontWeight: '700' },
  modalSave: { backgroundColor: '#F59E0B' },
  modalSaveText: { color: '#FFF', fontWeight: '700' },
});
