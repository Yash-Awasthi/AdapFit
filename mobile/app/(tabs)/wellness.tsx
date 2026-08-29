import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Animated,
  StyleSheet,
  Alert,
} from 'react-native';
import * as Haptics from 'expo-haptics';
import { Wind, Brain, TrendingUp, TrendingDown, Minus, Droplets, Plus, Clock, Angry, Frown, Meh, Smile, Laugh } from 'lucide-react-native';
import { SectionHeader } from '../../src/components';
import MeditationPlayer from '../../src/components/MeditationPlayer';
import { api } from '../../src/services/api';
import { API_BASE_URL } from '../../src/services/config';
import { useUserStore } from '../../src/stores';
import { useTheme } from '../../src/services/theme';
import { authHeader } from '../../src/services/authToken';

const API = API_BASE_URL;

interface BreathingExercise {
  id: string;
  name: string;
  description: string;
  inhale_sec: number;
  hold_sec: number;
  exhale_sec: number;
  rounds: number;
  benefit: string;
}

interface MoodTrend {
  avg_mood: number;
  avg_energy: number;
  avg_anxiety: number;
  mood_trend: string;
  count: number;
}

interface MeditationSessionSummary {
  id: string;
  name: string;
  category: string;
  duration_minutes: number;
  difficulty: string;
  benefits: string[];
  best_time: string;
  tags: string[];
  steps_count: number;
}

// index 0 unused, mood is logged 1-10; icon progresses through 5 expressions, color ramps red to green
const MOOD_ICONS = [Angry, Angry, Frown, Frown, Meh, Meh, Smile, Smile, Laugh, Laugh];
const MOOD_COLORS = ['#EF4444', '#F87171', '#FB923C', '#FBBF24', '#FACC15', '#A3E635', '#84CC16', '#4ADE80', '#22C55E', '#10B981'];
const TAGS = ['work_stress', 'good_sleep', 'social', 'exercise', 'meditation', 'nature'];
const QUICK_DRINKS = [
  { ml: 150, label: '150ml' },
  { ml: 250, label: '250ml' },
  { ml: 350, label: '350ml' },
  { ml: 500, label: '500ml' },
  { ml: 750, label: '750ml' },
];

export default function WellnessScreen() {
  const { theme } = useTheme();
  const s = makeStyles(theme);
  const userId = useUserStore((s) => s.userId);
  const [exercises, setExercises] = useState<BreathingExercise[]>([]);
  const [trend, setTrend] = useState<MoodTrend | null>(null);
  const [hydration, setHydration] = useState<{ total_ml: number; daily_goal_ml: number; progress_pct: number } | null>(null);
  const [selectedMood, setSelectedMood] = useState(5);
  const [selectedEnergy, setSelectedEnergy] = useState(5);
  const [selectedAnxiety, setSelectedAnxiety] = useState(5);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [logged, setLogged] = useState(false);
  const [activeBreathing, setActiveBreathing] = useState<string | null>(null);
  const [meditations, setMeditations] = useState<MeditationSessionSummary[]>([]);
  const [activeMeditation, setActiveMeditation] = useState<Awaited<ReturnType<typeof api.getMeditationSession>> | null>(null);
  const breathAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    try {
      const [exRes, trendRes, hydData, medData] = await Promise.all([
        fetch(`${API}/api/v1/mental-health/breathing-exercises`, { headers: authHeader() }),
        fetch(`${API}/api/v1/mental-health?user_id=${userId}&days=7`, { headers: authHeader() }),
        api.getHydrationToday(userId).catch(() => null),
        api.getMeditationSessions().catch(() => null),
      ]);
      if (exRes.ok) setExercises(await exRes.json());
      if (trendRes.ok) setTrend(await trendRes.json());
      if (hydData) setHydration(hydData);
      if (medData) setMeditations(medData.sessions);
    } catch {}
  }

  async function openMeditation(id: string) {
    try {
      const full = await api.getMeditationSession(id);
      setActiveMeditation(full);
    } catch {}
  }

  async function logWater(amount: number) {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    try {
      await api.logHydration(userId, amount, 'water');
      const updated = await api.getHydrationToday(userId);
      setHydration(updated);
    } catch (err: any) {
      Alert.alert('Could not log water', err?.message || String(err));
    }
  }

  async function logMood() {
    try {
      const res = await fetch(`${API}/api/v1/mental-health`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeader() },
        body: JSON.stringify({
          user_id: userId,
          mood: selectedMood,
          energy: selectedEnergy,
          anxiety: selectedAnxiety,
          tags: selectedTags,
        }),
      });
      if (res.ok) {
        setLogged(true);
        fetchData();
      } else {
        Alert.alert('Check-in failed', `Server returned ${res.status}.`);
      }
    } catch (err: any) {
      Alert.alert('Could not reach the server', err?.message || String(err));
    }
  }

  function toggleTag(tag: string) {
    Haptics.selectionAsync();
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  }

  function startBreathing(ex: BreathingExercise) {
    if (activeBreathing === ex.id) {
      setActiveBreathing(null);
      breathAnim.setValue(1);
      return;
    }
    setActiveBreathing(ex.id);
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    runBreathCycle(ex);
  }

  function runBreathCycle(ex: BreathingExercise) {
    let round = 0;
    const totalRounds = ex.rounds;
    const cycle = () => {
      if (round >= totalRounds || activeBreathing !== ex.id) {
        setActiveBreathing(null);
        breathAnim.setValue(1);
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        return;
      }
      Animated.timing(breathAnim, { toValue: 1.5, duration: ex.inhale_sec * 1000, useNativeDriver: true }).start(() => {
        if (ex.hold_sec > 0) {
          setTimeout(() => {
            Animated.timing(breathAnim, { toValue: 1, duration: ex.exhale_sec * 1000, useNativeDriver: true }).start(() => {
              round++;
              Haptics.selectionAsync();
              cycle();
            });
          }, ex.hold_sec * 1000);
        } else {
          Animated.timing(breathAnim, { toValue: 1, duration: ex.exhale_sec * 1000, useNativeDriver: true }).start(() => {
            round++;
            Haptics.selectionAsync();
            cycle();
          });
        }
      });
    };
    cycle();
  }

  const trendIcon = (trendStatus: string) => {
    if (trendStatus === 'improving') return <TrendingUp size={16} color={theme.success} />;
    if (trendStatus === 'declining') return <TrendingDown size={16} color={theme.danger} />;
    return <Minus size={16} color={theme.textMuted} />;
  };

  if (activeMeditation) {
    return (
      <MeditationPlayer
        session={activeMeditation}
        onComplete={() => setActiveMeditation(null)}
        onClose={() => setActiveMeditation(null)}
      />
    );
  }

  return (
    <ScrollView style={s.container} contentContainerStyle={{ paddingBottom: 100 }}>
      <Text style={s.title}>Wellness</Text>

      {/* Hydration Tracker Card */}
      <SectionHeader title="Daily Hydration" />
      <View style={s.hydrationCard}>
        <View style={s.hydrationHeader}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <Droplets size={20} color="#38BDF8" />
            <Text style={s.hydrationTitle}>Water Intake</Text>
          </View>
          <Text style={s.hydrationTotal}>
            {hydration?.total_ml ?? 0} / {hydration?.daily_goal_ml ?? 3000} ml
          </Text>
        </View>
        <View style={s.hydBarBg}>
          <View
            style={[
              s.hydBarFill,
              { width: `${Math.min(100, hydration?.progress_pct ?? 0)}%` },
            ]}
          />
        </View>
        <View style={s.quickHydRow}>
          {QUICK_DRINKS.map((d) => (
            <TouchableOpacity
              key={d.ml}
              style={s.hydBtn}
              onPress={() => logWater(d.ml)}
            >
              <Text style={s.hydBtnText}>+{d.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Mood Check-in */}
      <SectionHeader title="How are you feeling?" />

      <Text style={s.label}>Mood ({selectedMood}/10)</Text>
      <View style={s.slider}>
        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((v) => {
          const MoodIcon = MOOD_ICONS[v - 1];
          return (
            <TouchableOpacity
              key={v}
              style={[s.dot, selectedMood === v && s.dotActive]}
              onPress={() => { Haptics.selectionAsync(); setSelectedMood(v); }}
            >
              <MoodIcon size={selectedMood === v ? 20 : 16} color={selectedMood === v ? '#fff' : MOOD_COLORS[v - 1]} />
            </TouchableOpacity>
          );
        })}
      </View>

      <Text style={s.label}>Energy ({selectedEnergy}/10)</Text>
      <View style={s.slider}>
        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((v) => (
          <TouchableOpacity
            key={v}
            style={[s.dot, selectedEnergy === v && s.dotActive]}
            onPress={() => { Haptics.selectionAsync(); setSelectedEnergy(v); }}
          >
            <Text style={[s.dotNum, selectedEnergy === v && s.dotNumActive]}>{v}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={s.label}>Stress / Anxiety ({selectedAnxiety}/10)</Text>
      <View style={s.slider}>
        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((v) => (
          <TouchableOpacity
            key={v}
            style={[s.dot, selectedAnxiety === v && s.dotActive]}
            onPress={() => { Haptics.selectionAsync(); setSelectedAnxiety(v); }}
          >
            <Text style={[s.dotNum, selectedAnxiety === v && s.dotNumActive]}>{v}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={s.label}>Context Tags</Text>
      <View style={s.tagGrid}>
        {TAGS.map((tag) => (
          <TouchableOpacity
            key={tag}
            style={[s.tag, selectedTags.includes(tag) && s.tagActive]}
            onPress={() => toggleTag(tag)}
          >
            <Text style={[s.tagText, selectedTags.includes(tag) && s.tagTextActive]}>
              {tag.replace('_', ' ')}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <TouchableOpacity style={s.logButton} onPress={logMood}>
        <Text style={s.logButtonText}>{logged ? 'Updated!' : 'Log Check-in'}</Text>
      </TouchableOpacity>

      {/* Mood Trends */}
      {trend && trend.count > 0 && (
        <>
          <SectionHeader title="7-Day Trends" />
          <View style={s.trendCard}>
            <View style={s.trendRow}>
              <Text style={s.trendLabel}>Avg Mood</Text>
              <View style={s.trendValue}>
                <Text style={s.trendNum}>{trend.avg_mood.toFixed(1)}/10</Text>
                {trendIcon(trend.mood_trend)}
              </View>
            </View>
            <View style={s.trendRow}>
              <Text style={s.trendLabel}>Avg Energy</Text>
              <Text style={s.trendNum}>{trend.avg_energy.toFixed(1)}/10</Text>
            </View>
            <View style={s.trendRow}>
              <Text style={s.trendLabel}>Avg Anxiety</Text>
              <Text style={s.trendNum}>{trend.avg_anxiety.toFixed(1)}/10</Text>
            </View>
            <Text style={s.trendStatus}>Trend: {trend.mood_trend}</Text>
          </View>
        </>
      )}

      {/* Breathing Exercises */}
      <SectionHeader title="Breathing Exercises" />
      {exercises.map((ex) => (
        <TouchableOpacity
          key={ex.id}
          style={s.breathCard}
          onPress={() => startBreathing(ex)}
        >
          <View style={s.breathHeader}>
            <Wind size={20} color={theme.primaryLight} />
            <Text style={s.breathName}>{ex.name}</Text>
          </View>
          <Text style={s.breathDesc}>{ex.description}</Text>
          <View style={s.breathPattern}>
            <Text style={s.breathStep}>Inhale: {ex.inhale_sec}s</Text>
            {ex.hold_sec > 0 && <Text style={s.breathStep}>Hold: {ex.hold_sec}s</Text>}
            <Text style={s.breathStep}>Exhale: {ex.exhale_sec}s</Text>
            <Text style={s.breathStep}>{ex.rounds} rounds</Text>
          </View>
          <Text style={s.breathBenefit}>{ex.benefit}</Text>

          {activeBreathing === ex.id && (
            <View style={s.breathAnimation}>
              <Animated.View
                style={[
                  s.breathCircle,
                  { transform: [{ scale: breathAnim }] },
                ]}
              />
              <Text style={s.breathInstruction}>Follow the circle...</Text>
            </View>
          )}
        </TouchableOpacity>
      ))}

      {/* Meditation Sessions */}
      <SectionHeader title="Meditation" />
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 12 }}>
        {meditations.map((m) => (
          <TouchableOpacity key={m.id} style={s.medCard} onPress={() => openMeditation(m.id)}>
            <Brain size={20} color={theme.primaryLight} />
            <Text style={s.medName}>{m.name}</Text>
            <View style={s.medMetaRow}>
              <Clock size={12} color={theme.textMuted} />
              <Text style={s.medMeta}>{m.duration_minutes} min</Text>
            </View>
            <Text style={s.medMeta}>{m.difficulty}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </ScrollView>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.background, padding: 20 },
    title: { fontSize: 28, fontWeight: '700', color: theme.text, marginTop: 48, marginBottom: 16 },
    hydrationCard: {
      backgroundColor: theme.surface,
      borderRadius: 12,
      padding: 16,
      marginBottom: 20,
      borderLeftWidth: 4,
      borderLeftColor: '#38BDF8',
    },
    hydrationHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
    hydrationTitle: { fontSize: 16, fontWeight: '600', color: theme.text },
    hydrationTotal: { fontSize: 14, fontWeight: '700', color: '#38BDF8' },
    hydBarBg: { height: 8, backgroundColor: theme.background, borderRadius: 4, marginVertical: 12 },
    hydBarFill: { height: 8, backgroundColor: '#38BDF8', borderRadius: 4 },
    quickHydRow: { flexDirection: 'row', gap: 6, justifyContent: 'space-between' },
    hydBtn: {
      flex: 1,
      backgroundColor: theme.background,
      paddingVertical: 6,
      borderRadius: 6,
      alignItems: 'center',
      borderWidth: 1,
      borderColor: theme.border,
    },
    hydBtnText: { fontSize: 11, color: '#38BDF8', fontWeight: '600' },
    label: { fontSize: 14, fontWeight: '600', color: theme.textSecondary, marginBottom: 8, marginTop: 12 },
    slider: { flexDirection: 'row', gap: 4, marginBottom: 8 },
    dot: {
      flex: 1,
      height: 36,
      borderRadius: 8,
      backgroundColor: theme.surface,
      alignItems: 'center',
      justifyContent: 'center',
    },
    dotActive: { backgroundColor: theme.primary },
    dotText: { fontSize: 16 },
    dotTextActive: { transform: [{ scale: 1.2 }] },
    dotNum: { fontSize: 12, color: theme.textMuted },
    dotNumActive: { color: '#fff', fontWeight: '700' },
    tagGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 },
    tag: {
      paddingHorizontal: 12,
      paddingVertical: 6,
      borderRadius: 16,
      backgroundColor: theme.surface,
      borderWidth: 1,
      borderColor: theme.border,
    },
    tagActive: { backgroundColor: theme.primary, borderColor: theme.primary },
    tagText: { fontSize: 12, color: theme.textSecondary, textTransform: 'capitalize' },
    tagTextActive: { color: '#fff' },
    logButton: {
      backgroundColor: theme.primary,
      borderRadius: 12,
      padding: 16,
      alignItems: 'center',
      marginBottom: 24,
    },
    logButtonText: { color: '#fff', fontSize: 16, fontWeight: '700' },
    trendCard: {
      backgroundColor: theme.surface,
      borderRadius: 12,
      padding: 16,
      marginBottom: 16,
    },
    trendRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 8,
    },
    trendLabel: { fontSize: 14, color: theme.textSecondary },
    trendValue: { flexDirection: 'row', alignItems: 'center', gap: 6 },
    trendNum: { fontSize: 18, fontWeight: '700', color: theme.text },
    trendStatus: { fontSize: 12, color: theme.textMuted, marginTop: 4 },
    breathCard: {
      backgroundColor: theme.surface,
      borderRadius: 12,
      padding: 16,
      marginBottom: 12,
    },
    breathHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
    breathName: { fontSize: 16, fontWeight: '600', color: theme.text },
    breathDesc: { fontSize: 13, color: theme.textSecondary, marginBottom: 8, lineHeight: 18 },
    breathPattern: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 8 },
    breathStep: {
      fontSize: 12,
      color: theme.primaryLight,
      backgroundColor: theme.background,
      paddingHorizontal: 8,
      paddingVertical: 4,
      borderRadius: 8,
    },
    breathBenefit: { fontSize: 12, color: theme.textMuted, fontStyle: 'italic' },
    breathAnimation: {
      alignItems: 'center',
      padding: 24,
    },
    breathCircle: {
      width: 100,
      height: 100,
      borderRadius: 50,
      backgroundColor: 'rgba(129, 140, 248, 0.3)',
      borderWidth: 2,
      borderColor: theme.primaryLight,
    },
    breathInstruction: {
      fontSize: 14,
      color: theme.primaryLight,
      marginTop: 12,
      fontWeight: '500',
    },
    medCard: {
      backgroundColor: theme.surface,
      borderRadius: 12,
      padding: 16,
      marginRight: 12,
      width: 140,
      gap: 6,
    },
    medName: { fontSize: 14, fontWeight: '600', color: theme.text },
    medMetaRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
    medMeta: { fontSize: 12, color: theme.textMuted, textTransform: 'capitalize' },
  });
}
