/**
 * Cycle — period, fertility window, and phase-aware training in one screen.
 *
 * Cycle length is asked for rather than assumed: 28 days is only an average
 * and the phase boundaries, and therefore every recommendation below, shift
 * with it.
 */
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, TextInput,
  ActivityIndicator, RefreshControl, Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Calendar } from 'react-native-calendars';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { colors, spacing, radius } from '../../src/theme';
import { useTabBarHeight } from '../../src/theme/layout';
import { getJson, postJson, asArray } from '../../src/services/http';
import { useUserStore } from '../../src/stores';

const PHASES = {
  menstrual: { label: 'Menstrual', color: '#EF4444', icon: 'water' },
  follicular: { label: 'Follicular', color: '#22C55E', icon: 'leaf' },
  ovulation: { label: 'Ovulation', color: '#F59E0B', icon: 'sunny' },
  luteal: { label: 'Luteal', color: '#8B5CF6', icon: 'moon' },
} as const;

type PhaseName = keyof typeof PHASES;

interface CurrentCycle {
  has_cycle_data: boolean;
  current_phase?: { phase: PhaseName; day: number; days_remaining: number; performance_note: string };
  training_recommendation?: {
    intensity: string; volume_reduction_pct: number;
    recommended_types: string[]; note?: string;
  };
  nutrition_recommendation?: { focus?: string; foods?: string[]; note?: string };
  next_period_date?: string;
  cycle_length?: number;
}

interface CalendarDay { date: string; phase: PhaseName; day_in_cycle: number }

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function PhaseLegend() {
  return (
    <View style={styles.legend}>
      {(Object.keys(PHASES) as PhaseName[]).map((p) => (
        <View key={p} style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: PHASES[p].color }]} />
          <Text style={styles.legendText}>{PHASES[p].label}</Text>
        </View>
      ))}
    </View>
  );
}

function SetupCard({ userId, initialLength, onSaved }: {
  userId: string; initialLength: number; onSaved: () => void;
}) {
  const [startDate, setStartDate] = useState(todayIso());
  const [length, setLength] = useState(String(initialLength));
  const [periodLength, setPeriodLength] = useState('5');
  const [saving, setSaving] = useState(false);

  const save = async () => {
    const len = Number(length);
    const period = Number(periodLength);
    // The API rejects values outside these ranges, so catch them here and
    // say which field is wrong rather than failing the whole request.
    if (!Number.isFinite(len) || len < 20 || len > 40) {
      Alert.alert('Check cycle length', 'Enter a cycle length between 20 and 40 days.');
      return;
    }
    if (!Number.isFinite(period) || period < 2 || period > 10) {
      Alert.alert('Check period length', 'Enter a period length between 2 and 10 days.');
      return;
    }
    if (!/^\d{4}-\d{2}-\d{2}$/.test(startDate)) {
      Alert.alert('Check start date', 'Pick the first day of your last period on the calendar.');
      return;
    }

    setSaving(true);
    const saved = await postJson(`/cycle/log?user_id=${userId}`, {
      start_date: startDate, length_days: len, period_length_days: period,
    });
    setSaving(false);
    if (saved) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      onSaved();
    } else {
      Alert.alert('Could not save', 'Check your connection and try again.');
    }
  };

  return (
    <View style={styles.card}>
      <Text style={styles.cardTitle}>Set up your cycle</Text>
      <Text style={styles.cardBody}>
        Cycle length varies between people. Yours drives every phase and
        fertility estimate on this screen.
      </Text>

      <Text style={styles.fieldLabel}>First day of your last period</Text>
      <Calendar
        current={startDate}
        onDayPress={(d: { dateString: string }) => setStartDate(d.dateString)}
        markedDates={{ [startDate]: { selected: true, selectedColor: colors.primary } }}
        maxDate={todayIso()}
        theme={calendarTheme}
        style={styles.calendar}
      />

      <View style={styles.fieldRow}>
        <View style={styles.field}>
          <Text style={styles.fieldLabel}>Cycle length (days)</Text>
          <TextInput
            style={styles.input}
            value={length}
            onChangeText={setLength}
            keyboardType="number-pad"
            maxLength={2}
            accessibilityLabel="Cycle length in days"
          />
          <Text style={styles.fieldHint}>Usually 21–35</Text>
        </View>
        <View style={styles.field}>
          <Text style={styles.fieldLabel}>Period length (days)</Text>
          <TextInput
            style={styles.input}
            value={periodLength}
            onChangeText={setPeriodLength}
            keyboardType="number-pad"
            maxLength={2}
            accessibilityLabel="Period length in days"
          />
          <Text style={styles.fieldHint}>Usually 3–7</Text>
        </View>
      </View>

      <TouchableOpacity
        style={[styles.primaryButton, saving && styles.disabled]}
        onPress={save}
        disabled={saving}
        accessibilityRole="button"
      >
        {saving
          ? <ActivityIndicator size="small" color="#FFF" />
          : <Text style={styles.primaryButtonText}>Save cycle</Text>}
      </TouchableOpacity>
    </View>
  );
}

export default function CycleScreen() {
  const insets = useSafeAreaInsets();
  const tabBarHeight = useTabBarHeight();
  const userId = useUserStore((s) => s.userId);
  const [current, setCurrent] = useState<CurrentCycle | null>(null);
  const [days, setDays] = useState<CalendarDay[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [editing, setEditing] = useState(false);

  const load = useCallback(async () => {
    const [cur, cal] = await Promise.all([
      getJson<CurrentCycle>(`/cycle/current?user_id=${userId}`),
      getJson<{ calendar: CalendarDay[] }>(`/cycle/calendar?user_id=${userId}&months=3`),
    ]);
    setCurrent(cur);
    setDays(asArray<CalendarDay>(cal?.calendar));
    setLoading(false);
  }, [userId]);

  useEffect(() => { load(); }, [load]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }, [load]);

  const marked = useMemo(() => {
    const out: Record<string, any> = {};
    for (const d of days) {
      const phase = PHASES[d.phase];
      if (!phase) continue;
      out[d.date] = {
        customStyles: {
          container: { backgroundColor: phase.color + '33', borderRadius: 8 },
          text: { color: colors.text.primary, fontWeight: '600' },
        },
      };
    }
    const today = todayIso();
    out[today] = {
      ...(out[today] || {}),
      customStyles: {
        container: {
          backgroundColor: out[today]?.customStyles?.container?.backgroundColor || 'transparent',
          borderRadius: 8, borderWidth: 2, borderColor: colors.primaryLight,
        },
        text: { color: colors.text.primary, fontWeight: '800' },
      },
    };
    return out;
  }, [days]);

  const fertileWindow = useMemo(
    () => days.filter((d) => d.phase === 'ovulation').map((d) => d.date).sort(),
    [days]
  );

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  const hasData = Boolean(current?.has_cycle_data) && !editing;
  const phaseName = current?.current_phase?.phase;
  const phase = phaseName ? PHASES[phaseName] : null;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={{ paddingBottom: tabBarHeight + spacing.xl }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
      showsVerticalScrollIndicator={false}
    >
      <View style={[styles.header, { paddingTop: insets.top + spacing.xl }]}>
        <View style={{ flex: 1 }}>
          <Text style={styles.headerTitle}>Cycle</Text>
          <Text style={styles.headerSubtitle}>Phases, fertility window, and training fit</Text>
        </View>
        {hasData && (
          <TouchableOpacity
            style={styles.editButton}
            onPress={() => setEditing(true)}
            accessibilityLabel="Edit cycle settings"
          >
            <Ionicons name="settings-outline" size={18} color={colors.text.primary} />
          </TouchableOpacity>
        )}
      </View>

      {!hasData ? (
        <SetupCard
          userId={userId}
          initialLength={current?.cycle_length ?? 28}
          onSaved={() => { setEditing(false); setLoading(true); load(); }}
        />
      ) : (
        <>
          {phase && current?.current_phase && (
            <View style={[styles.card, { borderColor: phase.color + '55' }]}>
              <View style={styles.phaseTop}>
                <View style={[styles.phaseIcon, { backgroundColor: phase.color + '22' }]}>
                  <Ionicons name={phase.icon as any} size={22} color={phase.color} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.phaseName, { color: phase.color }]}>{phase.label} phase</Text>
                  <Text style={styles.phaseDay}>
                    Day {current.current_phase.day} of {current.cycle_length ?? 28}
                    {current.current_phase.days_remaining > 0
                      ? ` · ${current.current_phase.days_remaining}d left in phase`
                      : ''}
                  </Text>
                </View>
              </View>
              <Text style={styles.phaseNote}>{current.current_phase.performance_note}</Text>
              {current.next_period_date && (
                <View style={styles.nextRow}>
                  <Ionicons name="calendar-outline" size={14} color={colors.text.muted} />
                  <Text style={styles.nextText}>
                    Next period expected {current.next_period_date}
                  </Text>
                </View>
              )}
            </View>
          )}

          {fertileWindow.length > 0 && (
            <View style={styles.card}>
              <View style={styles.sectionRow}>
                <Ionicons name="flower-outline" size={18} color={PHASES.ovulation.color} />
                <Text style={styles.cardTitle}>Fertility window</Text>
              </View>
              <Text style={styles.cardBody}>
                Estimated most fertile days: {fertileWindow[0]} to {fertileWindow[fertileWindow.length - 1]}.
              </Text>
              <Text style={styles.disclaimer}>
                Estimated from cycle length alone. Not a contraceptive method.
              </Text>
            </View>
          )}

          <View style={styles.card}>
            <View style={styles.sectionRow}>
              <Ionicons name="calendar" size={18} color={colors.primary} />
              <Text style={styles.cardTitle}>Calendar</Text>
            </View>
            <Calendar
              markingType="custom"
              markedDates={marked}
              theme={calendarTheme}
              style={styles.calendar}
            />
            <PhaseLegend />
          </View>

          {current?.training_recommendation && (
            <View style={styles.card}>
              <View style={styles.sectionRow}>
                <Ionicons name="barbell-outline" size={18} color={colors.health.heart} />
                <Text style={styles.cardTitle}>Training this phase</Text>
              </View>
              <View style={styles.tagRow}>
                <View style={styles.tag}>
                  <Text style={styles.tagText}>
                    Intensity: {current.training_recommendation.intensity.replace(/_/g, ' ')}
                  </Text>
                </View>
                {current.training_recommendation.volume_reduction_pct > 0 && (
                  <View style={styles.tag}>
                    <Text style={styles.tagText}>
                      Volume −{current.training_recommendation.volume_reduction_pct}%
                    </Text>
                  </View>
                )}
              </View>
              {asArray<string>(current.training_recommendation.recommended_types).map((t) => (
                <View key={t} style={styles.bulletRow}>
                  <Ionicons name="ellipse" size={5} color={colors.text.muted} />
                  <Text style={styles.bulletText}>{t}</Text>
                </View>
              ))}
              {!!current.training_recommendation.note && (
                <Text style={styles.cardBody}>{current.training_recommendation.note}</Text>
              )}
            </View>
          )}

          {current?.nutrition_recommendation && (
            <View style={styles.card}>
              <View style={styles.sectionRow}>
                <Ionicons name="restaurant-outline" size={18} color={colors.health.nutrition} />
                <Text style={styles.cardTitle}>Nutrition this phase</Text>
              </View>
              {!!current.nutrition_recommendation.focus && (
                <Text style={styles.cardBody}>{current.nutrition_recommendation.focus}</Text>
              )}
              <View style={styles.tagRow}>
                {asArray<string>(current.nutrition_recommendation.foods).map((f) => (
                  <View key={f} style={styles.tag}>
                    <Text style={styles.tagText}>{f}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}
        </>
      )}
    </ScrollView>
  );
}

const calendarTheme = {
  backgroundColor: 'transparent',
  calendarBackground: 'transparent',
  textSectionTitleColor: colors.text.muted,
  dayTextColor: colors.text.secondary,
  todayTextColor: colors.primaryLight,
  monthTextColor: colors.text.primary,
  arrowColor: colors.primaryLight,
  textDisabledColor: colors.surface.border,
  textDayFontWeight: '500' as const,
  textMonthFontWeight: '700' as const,
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  center: { flex: 1, backgroundColor: colors.bg.deep, alignItems: 'center', justifyContent: 'center' },

  header: {
    flexDirection: 'row', alignItems: 'flex-end', gap: spacing.md,
    paddingHorizontal: spacing.screenPadding, paddingBottom: spacing.lg,
  },
  headerTitle: { fontSize: 28, fontWeight: '800', color: colors.text.primary, letterSpacing: -0.5 },
  headerSubtitle: { fontSize: 14, color: colors.text.muted, marginTop: 4 },
  editButton: {
    width: 40, height: 40, borderRadius: 20, backgroundColor: colors.bg.card,
    borderWidth: 1, borderColor: colors.surface.border,
    alignItems: 'center', justifyContent: 'center',
  },

  card: {
    marginHorizontal: spacing.screenPadding, marginBottom: spacing.lg,
    backgroundColor: colors.bg.card, borderRadius: radius.lg,
    borderWidth: 1, borderColor: colors.surface.border, padding: spacing.lg,
  },
  cardTitle: { fontSize: 16, fontWeight: '700', color: colors.text.primary },
  cardBody: { fontSize: 13, color: colors.text.secondary, lineHeight: 20, marginTop: spacing.sm },
  disclaimer: { fontSize: 11, color: colors.text.muted, marginTop: spacing.sm, fontStyle: 'italic' },
  sectionRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginBottom: spacing.xs },

  phaseTop: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  phaseIcon: { width: 44, height: 44, borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  phaseName: { fontSize: 17, fontWeight: '800' },
  phaseDay: { fontSize: 12, color: colors.text.muted, marginTop: 2 },
  phaseNote: { fontSize: 13, color: colors.text.secondary, lineHeight: 20, marginTop: spacing.md },
  nextRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: spacing.md },
  nextText: { fontSize: 12, color: colors.text.muted },

  calendar: { borderRadius: radius.md, marginTop: spacing.sm, backgroundColor: 'transparent' },
  legend: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md, marginTop: spacing.md },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  legendDot: { width: 10, height: 10, borderRadius: 5 },
  legendText: { fontSize: 11, color: colors.text.muted, fontWeight: '600' },

  fieldRow: { flexDirection: 'row', gap: spacing.md, marginTop: spacing.lg },
  field: { flex: 1 },
  fieldLabel: { fontSize: 12, fontWeight: '600', color: colors.text.secondary, marginTop: spacing.lg, marginBottom: spacing.xs },
  fieldHint: { fontSize: 11, color: colors.text.muted, marginTop: 4 },
  input: {
    backgroundColor: colors.bg.input, borderRadius: radius.input,
    borderWidth: 1, borderColor: colors.surface.border,
    paddingHorizontal: spacing.lg, height: 46,
    fontSize: 16, color: colors.text.primary,
  },

  primaryButton: {
    marginTop: spacing.xl, height: 48, borderRadius: radius.button,
    backgroundColor: colors.primary, alignItems: 'center', justifyContent: 'center',
  },
  primaryButtonText: { fontSize: 15, fontWeight: '700', color: '#FFF' },
  disabled: { opacity: 0.6 },

  tagRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginTop: spacing.md },
  tag: {
    backgroundColor: colors.surface.divider, borderRadius: radius.badge,
    paddingHorizontal: 10, paddingVertical: 5,
  },
  tagText: { fontSize: 11, color: colors.text.secondary, fontWeight: '600', textTransform: 'capitalize' },
  bulletRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginTop: spacing.sm },
  bulletText: { flex: 1, fontSize: 13, color: colors.text.secondary, textTransform: 'capitalize' },
});
