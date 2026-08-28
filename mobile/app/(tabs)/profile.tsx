import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronLeft } from 'lucide-react-native';
import { SectionHeader, LoadingScreen } from '../../src/components';
import { WorkoutHeatmap } from '../../src/components/WorkoutHeatmap';
import { useTheme } from '../../src/services/theme';
import { API_BASE_URL } from '../../src/services/config';

const API = API_BASE_URL;

interface HealthData {
  status: string;
  version: string;
  services: Record<string, any>;
}

function BodyMeasureRow({ label, apiPath, unit, userId, theme }: { label: string; apiPath: string; unit: string; userId: string; theme: any }) {
  const [value, setValue] = useState<string | null>(null);
  useEffect(() => {
    fetch(`${API}/api/v1/body/measurements?user_id=${userId}&days=1`)
      .then(r => r.ok ? r.json() : [])
      .then(items => {
        if (items.length > 0 && items[items.length - 1][apiPath] != null) {
          setValue(`${items[items.length - 1][apiPath]}${unit}`);
        }
      })
      .catch(() => {});
  }, []);
  return (
    <View style={styles.measureRow}>
      <Text style={[styles.measureLabel, { color: theme.textSecondary }]}>{label}</Text>
      <Text style={[styles.measureValue, { color: theme.text }]}>{value || '--'}</Text>
    </View>
  );
}

export default function ProfileScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [workoutDates, setWorkoutDates] = useState<string[]>([]);

  useEffect(() => {
    fetch(`${API}/health`)
      .then(r => r.ok ? r.json() : null)
      .then(setHealth)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingScreen />;

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
          <ChevronLeft size={22} color={theme.text} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: theme.text }]}>Body & System</Text>
        <View style={styles.backBtn} />
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        <SectionHeader title="Body Measurements" />
        <View style={[styles.card, { backgroundColor: theme.surface }]}>
          <BodyMeasureRow label="Weight" apiPath="weight_kg" unit="kg" userId="default" theme={theme} />
          <BodyMeasureRow label="Body Fat" apiPath="body_fat_pct" unit="%" userId="default" theme={theme} />
          <BodyMeasureRow label="Waist" apiPath="waist_cm" unit="cm" userId="default" theme={theme} />
          <BodyMeasureRow label="Muscle" apiPath="muscle_mass_kg" unit="kg" userId="default" theme={theme} />
        </View>

        <SectionHeader title="Workout History" />
        <WorkoutHeatmap workoutDates={workoutDates} />

        <SectionHeader title="System Status" />
        <View style={[styles.card, { backgroundColor: theme.surface }]}>
          <View style={styles.statusRow}>
            <View style={styles.statusIndicator}>
              <View style={[styles.dot, { backgroundColor: health?.status === 'healthy' ? theme.success : theme.danger }]} />
              <Text style={[styles.statusText, { color: theme.textSecondary }]}>Backend v{health?.version || '--'}</Text>
            </View>
            <Text style={[styles.statusValue, { color: theme.textMuted }]}>{health?.status || 'unknown'}</Text>
          </View>
          {health?.services && Object.entries(health.services).map(([name, svc]: [string, any]) => (
            <View key={name} style={styles.statusRow}>
              <View style={styles.statusIndicator}>
                <View style={[styles.dot, { backgroundColor: svc?.pytorch_available !== false || svc?.status !== 'unavailable' ? theme.success : theme.warning }]} />
                <Text style={[styles.statusText, { color: theme.textSecondary }]}>{name.replace('_', ' ')}</Text>
              </View>
              <Text style={[styles.statusValue, { color: theme.textMuted }]}>
                {svc?.model_trained ? 'trained' : svc?.status || 'active'}
              </Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 12, paddingTop: 56, paddingBottom: 12,
  },
  backBtn: { padding: 8, width: 38 },
  headerTitle: { fontSize: 17, fontWeight: '700' },
  content: { padding: 20, paddingBottom: 100 },
  card: { borderRadius: 12, padding: 16, marginBottom: 16 },
  measureRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8 },
  measureLabel: { fontSize: 14 },
  measureValue: { fontSize: 14, fontWeight: '600' },
  statusRow: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingVertical: 8,
  },
  statusIndicator: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  dot: { width: 8, height: 8, borderRadius: 4 },
  statusText: { fontSize: 13, textTransform: 'capitalize' },
  statusValue: { fontSize: 12 },
});
