import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { Moon, Flame, Zap, Wind } from 'lucide-react-native';
import { Button } from '../src/components';
import * as Haptics from 'expo-haptics';
import { API_BASE_URL } from '../src/services/config';
import { useUserStore } from '../src/stores';
import { useTheme } from '../src/services/theme';

const API = API_BASE_URL;

function SliderField({
  label,
  value,
  onChange,
  icon: Icon,
  min = 1,
  max = 10,
  leftLabel,
  rightLabel,
  color = '#818CF8',
  accessibilityLabel,
  accessibilityHint,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  icon: any;
  min?: number;
  max?: number;
  leftLabel: string;
  rightLabel: string;
  color?: string;
  accessibilityLabel?: string;
  accessibilityHint?: string;
}) {
  const { theme } = useTheme();
  const s = makeSliderStyles(theme);
  const values = Array.from({ length: max - min + 1 }, (_, i) => min + i);
  return (
    <View style={s.container} accessible accessibilityLabel={accessibilityLabel} accessibilityHint={accessibilityHint}>
      <View style={s.header}>
        <Icon size={18} color={color} />
        <Text style={s.label}>{label}</Text>
        <Text style={[s.value, { color }]}>{value}</Text>
      </View>
      <View style={s.row}>
        <Text style={s.endLabel}>{leftLabel}</Text>
        <View style={s.dots}>
          {values.map((v) => (
            <TouchableOpacity
              key={v}
              style={[
                s.dot,
                value === v && [s.dotActive, { backgroundColor: color }],
              ]}
              onPress={() => {
                Haptics.selectionAsync();
                onChange(v);
              }}
            >
              <Text
                style={[
                  s.dotText,
                  value === v && s.dotTextActive,
                ]}
              >
                {v}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
        <Text style={s.endLabel}>{rightLabel}</Text>
      </View>
    </View>
  );
}

export default function CheckinScreen() {
  const { theme } = useTheme();
  const s = makeStyles(theme);
  const userId = useUserStore((s) => s.userId);
  const [sleep, setSleep] = useState(8);
  const [soreness, setSoreness] = useState(5);
  const [fatigue, setFatigue] = useState(5);
  const [stress, setStress] = useState(5);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/recovery-logs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          log_date: new Date().toISOString().split('T')[0],
          subjective_checkin: {
            soreness,
            fatigue,
            stress,
            sore_muscle_groups: [],
          },
          wearable_data: {
            sleep_duration_hours: sleep,
          },
        }),
      });
      if (res.ok) {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        router.back();
      }
    } catch {}
    setLoading(false);
  }

  return (
    <ScrollView style={s.container}>
      <Text style={s.title} accessibilityRole="header">Morning Check-in</Text>
      <Text style={s.subtitle}>Rate how you're feeling right now</Text>

      <SliderField
        label="Sleep Hours"
        value={sleep}
        onChange={setSleep}
        icon={Moon}
        min={3}
        max={12}
        leftLabel="3h"
        rightLabel="12h"
        color={theme.primaryLight}
        accessibilityLabel={`Sleep hours: ${sleep}`}
        accessibilityHint="Slider from 3 to 12 hours"
      />

      <SliderField
        label="Soreness"
        value={soreness}
        onChange={setSoreness}
        icon={Flame}
        min={1}
        max={10}
        leftLabel="Sore"
        rightLabel="Fresh"
        color={theme.success}
        accessibilityLabel={`Soreness level: ${soreness} out of 10`}
        accessibilityHint="1 is very sore, 10 is completely fresh"
      />

      <SliderField
        label="Energy"
        value={fatigue}
        onChange={setFatigue}
        icon={Zap}
        min={1}
        max={10}
        leftLabel="Drained"
        rightLabel="Energized"
        color={theme.warning}
      />

      <SliderField
        label="Stress"
        value={stress}
        onChange={setStress}
        icon={Wind}
        min={1}
        max={10}
        leftLabel="Relaxed"
        rightLabel="Stressed"
        color={theme.danger}
      />

      <Button
        title="Submit Check-in"
        onPress={handleSubmit}
        loading={loading}
      />
    </ScrollView>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.background, padding: 20 },
    title: { fontSize: 24, fontWeight: '700', color: theme.text, marginTop: 48, marginBottom: 4 },
    subtitle: { fontSize: 14, color: theme.textMuted, marginBottom: 24 },
  });
}

function makeSliderStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { marginBottom: 24 },
    header: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
    label: { fontSize: 15, fontWeight: '600', color: theme.text, flex: 1 },
    value: { fontSize: 18, fontWeight: '700' },
    row: { flexDirection: 'row', alignItems: 'center' },
    endLabel: { fontSize: 10, color: theme.textMuted, width: 40 },
    dots: { flex: 1, flexDirection: 'row', justifyContent: 'space-between' },
    dot: {
      width: 30, height: 30, borderRadius: 15,
      backgroundColor: theme.surface, alignItems: 'center', justifyContent: 'center',
      borderWidth: 1, borderColor: theme.border,
    },
    dotActive: { borderColor: 'transparent' },
    dotText: { fontSize: 11, fontWeight: '600', color: theme.textMuted },
    dotTextActive: { color: '#fff' },
  });
}
