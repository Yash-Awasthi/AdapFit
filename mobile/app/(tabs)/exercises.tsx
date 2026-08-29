import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  Image,
  Modal,
  TextInput,
  StyleSheet,
  ScrollView,
} from 'react-native';
import { Search, Bookmark, BookmarkCheck, X, Calculator, Sparkles } from 'lucide-react-native';
import { LoadingScreen, EmptyState } from '../../src/components';
import { useBookmarkStore } from '../../src/stores';
import * as Haptics from 'expo-haptics';
import { API_BASE_URL } from '../../src/services/config';
import { useTheme } from '../../src/services/theme';
import { authHeader } from '../../src/services/authToken';

const API = API_BASE_URL;

interface Exercise {
  id: string;
  name: string;
  category: string;
  primary_muscles: string[];
  secondary_muscles?: string[];
  equipment: string;
  gif_url?: string;
  instructions?: string[];
  axial_loading_rating: number;
}

const CATEGORIES = ['all', 'strength', 'stretching', 'cardio'];
const MUSCLES = ['all', 'chest', 'back', 'shoulders', 'biceps', 'triceps', 'quads', 'hamstrings', 'glutes', 'core'];

export default function ExercisesScreen() {
  const { theme } = useTheme();
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedMuscle, setSelectedMuscle] = useState('all');
  const [total, setTotal] = useState(0);
  const [selectedExercise, setSelectedExercise] = useState<Exercise | null>(null);
  
  // 1RM Calculator State
  const [calcWeight, setCalcWeight] = useState('80');
  const [calcReps, setCalcReps] = useState('8');

  const { toggle, isBookmarked } = useBookmarkStore();

  useEffect(() => {
    fetchExercises();
  }, [selectedCategory, selectedMuscle]);

  async function fetchExercises() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedCategory !== 'all') params.set('category', selectedCategory);
      if (selectedMuscle !== 'all') params.set('muscle', selectedMuscle);
      params.set('page_size', '50');

      const res = await fetch(`${API}/api/v1/exercises?${params}`, { headers: authHeader() });
      if (res.ok) {
        const json = await res.json();
        setExercises(json.items || []);
        setTotal(json.total || 0);
      }
    } catch {}
    setLoading(false);
  }

  // 1RM Formulas (Epley & Brzycki)
  const weight = parseFloat(calcWeight) || 0;
  const reps = parseInt(calcReps, 10) || 1;
  const oneRepMax = reps === 1 ? weight : Math.round(weight * (1 + reps / 30));
  const threeRepMax = Math.round(oneRepMax * 0.93);
  const fiveRepMax = Math.round(oneRepMax * 0.87);
  const eightRepMax = Math.round(oneRepMax * 0.80);
  const tenRepMax = Math.round(oneRepMax * 0.75);

  const s = makeStyles(theme);

  return (
    <View style={s.container}>
      <View style={s.header}>
        <Text style={s.title}>Exercises</Text>
        <Text style={s.count}>{total} exercises</Text>
      </View>

      {/* Category Filter */}
      <FlatList
        horizontal
        data={CATEGORIES}
        keyExtractor={(item) => item}
        showsHorizontalScrollIndicator={false}
        style={s.filterRow}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[s.filterChip, selectedCategory === item && s.filterChipActive]}
            onPress={() => {
              Haptics.selectionAsync();
              setSelectedCategory(item);
            }}
          >
            <Text style={[s.filterText, selectedCategory === item && s.filterTextActive]}>
              {item}
            </Text>
          </TouchableOpacity>
        )}
      />

      {/* Muscle Filter */}
      <FlatList
        horizontal
        data={MUSCLES}
        keyExtractor={(item) => item}
        showsHorizontalScrollIndicator={false}
        style={s.filterRow}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[s.filterChip, selectedMuscle === item && s.filterChipActive]}
            onPress={() => {
              Haptics.selectionAsync();
              setSelectedMuscle(item);
            }}
          >
            <Text style={[s.filterText, selectedMuscle === item && s.filterTextActive]}>
              {item}
            </Text>
          </TouchableOpacity>
        )}
      />

      {loading ? (
        <LoadingScreen />
      ) : exercises.length === 0 ? (
        <EmptyState title="No Exercises" message="Try different filters." />
      ) : (
        <FlatList
          data={exercises}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={s.exerciseCard}
              onPress={() => {
                Haptics.selectionAsync();
                setSelectedExercise(item);
              }}
            >
              {item.gif_url ? (
                <Image source={{ uri: item.gif_url }} style={s.exerciseImage} />
              ) : (
                <View style={[s.exerciseImage, s.placeholder]}>
                  <Text style={s.placeholderText}>{item.name.charAt(0)}</Text>
                </View>
              )}
              <View style={s.exerciseInfo}>
                <Text style={s.exerciseName}>{item.name}</Text>
                <Text style={s.exerciseMuscle}>{item.primary_muscles.join(', ')}</Text>
                <View style={s.exerciseMeta}>
                  <Text style={s.metaText}>{item.equipment}</Text>
                  <Text style={s.metaText}>Axial: {item.axial_loading_rating}/5</Text>
                </View>
              </View>
              <TouchableOpacity
                style={s.bookmarkButton}
                onPress={() => {
                  Haptics.selectionAsync();
                  toggle(item.id);
                }}
              >
                {isBookmarked(item.id) ? (
                  <BookmarkCheck size={20} color={theme.primaryLight} />
                ) : (
                  <Bookmark size={20} color={theme.textMuted} />
                )}
              </TouchableOpacity>
            </TouchableOpacity>
          )}
          contentContainerStyle={s.list}
        />
      )}

      {/* Exercise Detail & 1RM Modal */}
      {selectedExercise && (
        <Modal visible={!!selectedExercise} transparent animationType="slide">
          <View style={s.modalOverlay}>
            <View style={s.modalCard}>
              <View style={s.modalHeader}>
                <Text style={s.modalTitle} numberOfLines={1}>
                  {selectedExercise.name}
                </Text>
                <TouchableOpacity onPress={() => setSelectedExercise(null)}>
                  <X size={22} color={theme.textSecondary} />
                </TouchableOpacity>
              </View>

              <ScrollView showsVerticalScrollIndicator={false}>
                {selectedExercise.gif_url && (
                  <Image
                    source={{ uri: selectedExercise.gif_url }}
                    style={s.modalImage}
                  />
                )}

                <View style={s.modalTags}>
                  <Text style={s.tagBadge}>
                    Muscles: {selectedExercise.primary_muscles.join(', ')}
                  </Text>
                  <Text style={s.tagBadge}>
                    Equipment: {selectedExercise.equipment}
                  </Text>
                  <Text style={s.tagBadge}>
                    Axial Load: {selectedExercise.axial_loading_rating}/5
                  </Text>
                </View>

                {/* 1RM Calculator Card */}
                <View style={s.calcCard}>
                  <View style={s.calcHeader}>
                    <Calculator size={18} color={theme.primaryLight} />
                    <Text style={s.calcTitle}>1RM Load Estimator</Text>
                  </View>

                  <View style={s.calcInputs}>
                    <View style={s.calcInputCol}>
                      <Text style={s.calcLabel}>Weight (kg)</Text>
                      <TextInput
                        style={s.calcField}
                        value={calcWeight}
                        onChangeText={setCalcWeight}
                        keyboardType="numeric"
                      />
                    </View>
                    <View style={s.calcInputCol}>
                      <Text style={s.calcLabel}>Reps Completed</Text>
                      <TextInput
                        style={s.calcField}
                        value={calcReps}
                        onChangeText={setCalcReps}
                        keyboardType="numeric"
                      />
                    </View>
                  </View>

                  <View style={s.repMaxGrid}>
                    <View style={s.repMaxBoxHighlight}>
                      <Text style={s.repMaxLabel}>Est. 1RM</Text>
                      <Text style={s.repMaxValHighlight}>{oneRepMax} kg</Text>
                    </View>
                    <View style={s.repMaxBox}>
                      <Text style={s.repMaxLabel}>3RM (93%)</Text>
                      <Text style={s.repMaxVal}>{threeRepMax} kg</Text>
                    </View>
                    <View style={s.repMaxBox}>
                      <Text style={s.repMaxLabel}>5RM (87%)</Text>
                      <Text style={s.repMaxVal}>{fiveRepMax} kg</Text>
                    </View>
                    <View style={s.repMaxBox}>
                      <Text style={s.repMaxLabel}>8RM (80%)</Text>
                      <Text style={s.repMaxVal}>{eightRepMax} kg</Text>
                    </View>
                    <View style={s.repMaxBox}>
                      <Text style={s.repMaxLabel}>10RM (75%)</Text>
                      <Text style={s.repMaxVal}>{tenRepMax} kg</Text>
                    </View>
                  </View>
                </View>
              </ScrollView>
            </View>
          </View>
        </Modal>
      )}
    </View>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.background, padding: 20 },
    header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline', marginTop: 48, marginBottom: 12 },
    title: { fontSize: 28, fontWeight: '700', color: theme.text },
    count: { fontSize: 14, color: theme.textMuted },
    filterRow: { marginBottom: 8, maxHeight: 40 },
    filterChip: {
      paddingHorizontal: 14, paddingVertical: 6, borderRadius: 16,
      backgroundColor: theme.surface, marginRight: 8, borderWidth: 1, borderColor: theme.border,
    },
    filterChipActive: { backgroundColor: theme.primary, borderColor: theme.primary },
    filterText: { fontSize: 13, color: theme.textSecondary, textTransform: 'capitalize' },
    filterTextActive: { color: '#fff', fontWeight: '600' },
    list: { paddingBottom: 100 },
    exerciseCard: {
      flexDirection: 'row', backgroundColor: theme.surface, borderRadius: 12,
      padding: 12, marginBottom: 8, alignItems: 'center',
    },
    exerciseImage: { width: 60, height: 60, borderRadius: 8, marginRight: 12 },
    placeholder: { backgroundColor: theme.surfaceHover, alignItems: 'center', justifyContent: 'center' },
    placeholderText: { fontSize: 24, fontWeight: '700', color: theme.primaryLight },
    exerciseInfo: { flex: 1 },
    exerciseName: { fontSize: 15, fontWeight: '600', color: theme.text },
    exerciseMuscle: { fontSize: 12, color: theme.primaryLight, marginTop: 2 },
    exerciseMeta: { flexDirection: 'row', gap: 12, marginTop: 4 },
    metaText: { fontSize: 11, color: theme.textMuted },
    bookmarkButton: { padding: 8 },

    // Modal Styles
    modalOverlay: {
      flex: 1,
      backgroundColor: 'rgba(15, 23, 42, 0.85)',
      justifyContent: 'flex-end',
    },
    modalCard: {
      backgroundColor: theme.surface,
      borderTopLeftRadius: 24,
      borderTopRightRadius: 24,
      padding: 20,
      maxHeight: '85%',
    },
    modalHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 16,
    },
    modalTitle: { fontSize: 20, fontWeight: '700', color: theme.text, flex: 1, marginRight: 12 },
    modalImage: { width: '100%', height: 220, borderRadius: 12, marginBottom: 16 },
    modalTags: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 },
    tagBadge: {
      backgroundColor: theme.background,
      paddingHorizontal: 10,
      paddingVertical: 6,
      borderRadius: 8,
      fontSize: 12,
      color: theme.primaryLight,
      borderWidth: 1,
      borderColor: theme.border,
    },
    calcCard: {
      backgroundColor: theme.background,
      borderRadius: 12,
      padding: 16,
      borderWidth: 1,
      borderColor: theme.border,
      marginBottom: 24,
    },
    calcHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
    calcTitle: { fontSize: 15, fontWeight: '600', color: theme.text },
    calcInputs: { flexDirection: 'row', gap: 12, marginBottom: 16 },
    calcInputCol: { flex: 1 },
    calcLabel: { fontSize: 12, color: theme.textSecondary, marginBottom: 4 },
    calcField: {
      backgroundColor: theme.surface,
      borderRadius: 8,
      padding: 10,
      fontSize: 16,
      color: theme.text,
      fontWeight: '600',
      borderWidth: 1,
      borderColor: theme.border,
      textAlign: 'center',
    },
    repMaxGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
    repMaxBoxHighlight: {
      flex: 1,
      minWidth: '45%',
      backgroundColor: theme.primaryBg,
      borderColor: theme.primary,
      borderWidth: 1,
      borderRadius: 8,
      padding: 8,
      alignItems: 'center',
    },
    repMaxBox: {
      flex: 1,
      minWidth: '28%',
      backgroundColor: theme.surface,
      borderRadius: 8,
      padding: 8,
      alignItems: 'center',
    },
    repMaxLabel: { fontSize: 11, color: theme.textSecondary, marginBottom: 2 },
    repMaxValHighlight: { fontSize: 16, fontWeight: '800', color: theme.primaryLight },
    repMaxVal: { fontSize: 14, fontWeight: '700', color: theme.textSecondary },
  });
}
