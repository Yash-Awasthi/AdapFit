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

      const res = await fetch(`${API}/api/v1/exercises?${params}`);
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

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Exercises</Text>
        <Text style={styles.count}>{total} exercises</Text>
      </View>

      {/* Category Filter */}
      <FlatList
        horizontal
        data={CATEGORIES}
        keyExtractor={(item) => item}
        showsHorizontalScrollIndicator={false}
        style={styles.filterRow}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[styles.filterChip, selectedCategory === item && styles.filterChipActive]}
            onPress={() => {
              Haptics.selectionAsync();
              setSelectedCategory(item);
            }}
          >
            <Text style={[styles.filterText, selectedCategory === item && styles.filterTextActive]}>
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
        style={styles.filterRow}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[styles.filterChip, selectedMuscle === item && styles.filterChipActive]}
            onPress={() => {
              Haptics.selectionAsync();
              setSelectedMuscle(item);
            }}
          >
            <Text style={[styles.filterText, selectedMuscle === item && styles.filterTextActive]}>
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
              style={styles.exerciseCard}
              onPress={() => {
                Haptics.selectionAsync();
                setSelectedExercise(item);
              }}
            >
              {item.gif_url ? (
                <Image source={{ uri: item.gif_url }} style={styles.exerciseImage} />
              ) : (
                <View style={[styles.exerciseImage, styles.placeholder]}>
                  <Text style={styles.placeholderText}>{item.name.charAt(0)}</Text>
                </View>
              )}
              <View style={styles.exerciseInfo}>
                <Text style={styles.exerciseName}>{item.name}</Text>
                <Text style={styles.exerciseMuscle}>{item.primary_muscles.join(', ')}</Text>
                <View style={styles.exerciseMeta}>
                  <Text style={styles.metaText}>{item.equipment}</Text>
                  <Text style={styles.metaText}>Axial: {item.axial_loading_rating}/5</Text>
                </View>
              </View>
              <TouchableOpacity
                style={styles.bookmarkButton}
                onPress={() => {
                  Haptics.selectionAsync();
                  toggle(item.id);
                }}
              >
                {isBookmarked(item.id) ? (
                  <BookmarkCheck size={20} color="#818CF8" />
                ) : (
                  <Bookmark size={20} color="#8B96AB" />
                )}
              </TouchableOpacity>
            </TouchableOpacity>
          )}
          contentContainerStyle={styles.list}
        />
      )}

      {/* Exercise Detail & 1RM Modal */}
      {selectedExercise && (
        <Modal visible={!!selectedExercise} transparent animationType="slide">
          <View style={styles.modalOverlay}>
            <View style={styles.modalCard}>
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle} numberOfLines={1}>
                  {selectedExercise.name}
                </Text>
                <TouchableOpacity onPress={() => setSelectedExercise(null)}>
                  <X size={22} color="#94A3B8" />
                </TouchableOpacity>
              </View>

              <ScrollView showsVerticalScrollIndicator={false}>
                {selectedExercise.gif_url && (
                  <Image
                    source={{ uri: selectedExercise.gif_url }}
                    style={styles.modalImage}
                  />
                )}

                <View style={styles.modalTags}>
                  <Text style={styles.tagBadge}>
                    Muscles: {selectedExercise.primary_muscles.join(', ')}
                  </Text>
                  <Text style={styles.tagBadge}>
                    Equipment: {selectedExercise.equipment}
                  </Text>
                  <Text style={styles.tagBadge}>
                    Axial Load: {selectedExercise.axial_loading_rating}/5
                  </Text>
                </View>

                {/* 1RM Calculator Card */}
                <View style={styles.calcCard}>
                  <View style={styles.calcHeader}>
                    <Calculator size={18} color="#818CF8" />
                    <Text style={styles.calcTitle}>1RM Load Estimator</Text>
                  </View>

                  <View style={styles.calcInputs}>
                    <View style={styles.calcInputCol}>
                      <Text style={styles.calcLabel}>Weight (kg)</Text>
                      <TextInput
                        style={styles.calcField}
                        value={calcWeight}
                        onChangeText={setCalcWeight}
                        keyboardType="numeric"
                      />
                    </View>
                    <View style={styles.calcInputCol}>
                      <Text style={styles.calcLabel}>Reps Completed</Text>
                      <TextInput
                        style={styles.calcField}
                        value={calcReps}
                        onChangeText={setCalcReps}
                        keyboardType="numeric"
                      />
                    </View>
                  </View>

                  <View style={styles.repMaxGrid}>
                    <View style={styles.repMaxBoxHighlight}>
                      <Text style={styles.repMaxLabel}>Est. 1RM</Text>
                      <Text style={styles.repMaxValHighlight}>{oneRepMax} kg</Text>
                    </View>
                    <View style={styles.repMaxBox}>
                      <Text style={styles.repMaxLabel}>3RM (93%)</Text>
                      <Text style={styles.repMaxVal}>{threeRepMax} kg</Text>
                    </View>
                    <View style={styles.repMaxBox}>
                      <Text style={styles.repMaxLabel}>5RM (87%)</Text>
                      <Text style={styles.repMaxVal}>{fiveRepMax} kg</Text>
                    </View>
                    <View style={styles.repMaxBox}>
                      <Text style={styles.repMaxLabel}>8RM (80%)</Text>
                      <Text style={styles.repMaxVal}>{eightRepMax} kg</Text>
                    </View>
                    <View style={styles.repMaxBox}>
                      <Text style={styles.repMaxLabel}>10RM (75%)</Text>
                      <Text style={styles.repMaxVal}>{tenRepMax} kg</Text>
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

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0F172A', padding: 20 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline', marginTop: 48, marginBottom: 12 },
  title: { fontSize: 28, fontWeight: '700', color: '#F8FAFC' },
  count: { fontSize: 14, color: '#8B96AB' },
  filterRow: { marginBottom: 8, maxHeight: 40 },
  filterChip: {
    paddingHorizontal: 14, paddingVertical: 6, borderRadius: 16,
    backgroundColor: '#1E293B', marginRight: 8, borderWidth: 1, borderColor: '#334155',
  },
  filterChipActive: { backgroundColor: '#4F46E5', borderColor: '#4F46E5' },
  filterText: { fontSize: 13, color: '#94A3B8', textTransform: 'capitalize' },
  filterTextActive: { color: '#fff', fontWeight: '600' },
  list: { paddingBottom: 100 },
  exerciseCard: {
    flexDirection: 'row', backgroundColor: '#1E293B', borderRadius: 12,
    padding: 12, marginBottom: 8, alignItems: 'center',
  },
  exerciseImage: { width: 60, height: 60, borderRadius: 8, marginRight: 12 },
  placeholder: { backgroundColor: '#334155', alignItems: 'center', justifyContent: 'center' },
  placeholderText: { fontSize: 24, fontWeight: '700', color: '#818CF8' },
  exerciseInfo: { flex: 1 },
  exerciseName: { fontSize: 15, fontWeight: '600', color: '#F8FAFC' },
  exerciseMuscle: { fontSize: 12, color: '#818CF8', marginTop: 2 },
  exerciseMeta: { flexDirection: 'row', gap: 12, marginTop: 4 },
  metaText: { fontSize: 11, color: '#8B96AB' },
  bookmarkButton: { padding: 8 },

  // Modal Styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(15, 23, 42, 0.85)',
    justifyContent: 'flex-end',
  },
  modalCard: {
    backgroundColor: '#1E293B',
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
  modalTitle: { fontSize: 20, fontWeight: '700', color: '#F8FAFC', flex: 1, marginRight: 12 },
  modalImage: { width: '100%', height: 220, borderRadius: 12, marginBottom: 16 },
  modalTags: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 },
  tagBadge: {
    backgroundColor: '#0F172A',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    fontSize: 12,
    color: '#818CF8',
    borderWidth: 1,
    borderColor: '#334155',
  },
  calcCard: {
    backgroundColor: '#0F172A',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#334155',
    marginBottom: 24,
  },
  calcHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  calcTitle: { fontSize: 15, fontWeight: '600', color: '#F8FAFC' },
  calcInputs: { flexDirection: 'row', gap: 12, marginBottom: 16 },
  calcInputCol: { flex: 1 },
  calcLabel: { fontSize: 12, color: '#94A3B8', marginBottom: 4 },
  calcField: {
    backgroundColor: '#1E293B',
    borderRadius: 8,
    padding: 10,
    fontSize: 16,
    color: '#F8FAFC',
    fontWeight: '600',
    borderWidth: 1,
    borderColor: '#334155',
    textAlign: 'center',
  },
  repMaxGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  repMaxBoxHighlight: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: '#1E1B4B',
    borderColor: '#4F46E5',
    borderWidth: 1,
    borderRadius: 8,
    padding: 8,
    alignItems: 'center',
  },
  repMaxBox: {
    flex: 1,
    minWidth: '28%',
    backgroundColor: '#1E293B',
    borderRadius: 8,
    padding: 8,
    alignItems: 'center',
  },
  repMaxLabel: { fontSize: 11, color: '#94A3B8', marginBottom: 2 },
  repMaxValHighlight: { fontSize: 16, fontWeight: '800', color: '#818CF8' },
  repMaxVal: { fontSize: 14, fontWeight: '700', color: '#CBD5E1' },
});
