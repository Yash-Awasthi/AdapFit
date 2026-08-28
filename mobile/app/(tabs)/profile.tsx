import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { Camera } from 'lucide-react-native';
import * as ImagePicker from 'expo-image-picker';
import { SectionHeader, LoadingScreen, ScreenHeader } from '../../src/components';
import { WorkoutHeatmap } from '../../src/components/WorkoutHeatmap';
import PersonalBestsWall from '../../src/components/PersonalBestsWall';
import { PhotoComparison } from '../../src/components/PhotoComparison';
import { useTheme } from '../../src/services/theme';
import { useUserStore } from '../../src/stores/userStore';
import { API_BASE_URL } from '../../src/services/config';

const API = API_BASE_URL;

interface HealthData {
  status: string;
  version: string;
  services: Record<string, any>;
}

interface ProgressPhoto {
  photo_uri: string;
  date: string;
  weight_kg?: number;
  body_fat_pct?: number;
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
  }, [userId]);
  return (
    <View style={styles.measureRow}>
      <Text style={[styles.measureLabel, { color: theme.textSecondary }]}>{label}</Text>
      <Text style={[styles.measureValue, { color: theme.text }]}>{value || '--'}</Text>
    </View>
  );
}

export default function ProfileScreen() {
  const { theme } = useTheme();
  const userId = useUserStore((s) => s.userId);
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [workoutDates, setWorkoutDates] = useState<string[]>([]);
  const [beforePhoto, setBeforePhoto] = useState<ProgressPhoto | null>(null);
  const [afterPhoto, setAfterPhoto] = useState<ProgressPhoto | null>(null);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);

  useEffect(() => {
    fetch(`${API}/health`)
      .then(r => r.ok ? r.json() : null)
      .then(setHealth)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const loadPhotoCompare = () => {
    fetch(`${API}/api/v1/progress-photos/compare?user_id=${userId}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        setBeforePhoto(d?.before || null);
        setAfterPhoto(d?.after || null);
      })
      .catch(() => {});
  };

  useEffect(() => { loadPhotoCompare(); }, [userId]);

  const capturePhoto = async () => {
    const perm = await ImagePicker.requestCameraPermissionsAsync();
    if (!perm.granted) {
      Alert.alert('Camera permission needed', 'Enable camera access to log a progress photo.');
      return;
    }
    const result = await ImagePicker.launchCameraAsync({ quality: 0.5 });
    if (result.canceled || !result.assets?.[0]?.uri) return;

    setUploadingPhoto(true);
    try {
      const res = await fetch(`${API}/api/v1/progress-photos?user_id=${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ photo_uri: result.assets[0].uri, angle: 'front' }),
      });
      if (res.ok) {
        loadPhotoCompare();
      } else {
        const detail = await res.text().catch(() => '');
        Alert.alert("Couldn't save photo", `Server returned ${res.status}.${detail ? ` ${detail.slice(0, 200)}` : ''}`);
      }
    } catch (err: any) {
      Alert.alert("Couldn't save photo", err?.message || String(err));
    }
    setUploadingPhoto(false);
  };

  if (loading) return <LoadingScreen />;

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      <ScreenHeader title="Body & System" />

      <ScrollView contentContainerStyle={styles.content}>
        <SectionHeader title="Body Measurements" />
        <View style={[styles.card, { backgroundColor: theme.surface }]}>
          <BodyMeasureRow label="Weight" apiPath="weight_kg" unit="kg" userId={userId} theme={theme} />
          <BodyMeasureRow label="Body Fat" apiPath="body_fat_pct" unit="%" userId={userId} theme={theme} />
          <BodyMeasureRow label="Waist" apiPath="waist_cm" unit="cm" userId={userId} theme={theme} />
          <BodyMeasureRow label="Muscle" apiPath="muscle_mass_kg" unit="kg" userId={userId} theme={theme} />
        </View>

        <SectionHeader title="Progress Photos" />
        <View style={[styles.card, { backgroundColor: theme.surface }]}>
          <PhotoComparison
            beforeUri={beforePhoto?.photo_uri}
            afterUri={afterPhoto?.photo_uri}
            beforeDate={beforePhoto?.date}
            afterDate={afterPhoto?.date}
            beforeWeight={beforePhoto?.weight_kg}
            afterWeight={afterPhoto?.weight_kg}
            beforeBodyFat={beforePhoto?.body_fat_pct}
            afterBodyFat={afterPhoto?.body_fat_pct}
          />
          <TouchableOpacity
            style={[styles.photoButton, { backgroundColor: theme.primary }]}
            onPress={capturePhoto}
            disabled={uploadingPhoto}
          >
            {uploadingPhoto ? (
              <ActivityIndicator size="small" color="#FFF" />
            ) : (
              <>
                <Camera size={16} color="#FFF" />
                <Text style={styles.photoButtonText}>Add Photo</Text>
              </>
            )}
          </TouchableOpacity>
        </View>

        <SectionHeader title="Personal Bests" />
        <PersonalBestsWall userId={userId} />

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
  photoButton: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6,
    borderRadius: 8, paddingVertical: 10, marginTop: 4,
  },
  photoButtonText: { fontSize: 13, fontWeight: '600', color: '#FFF' },
});
