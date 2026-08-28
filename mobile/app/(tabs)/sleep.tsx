import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native';
import { Moon, Plus, Trash2, TrendingUp, TrendingDown, Minus } from 'lucide-react-native';
import Svg, { Circle, Rect } from 'react-native-svg';
import * as Haptics from 'expo-haptics';
import { LoadingScreen } from '../../src/components';
import { API_BASE_URL } from '../../src/services/config';
import { useUserStore } from '../../src/stores';
import { useTheme } from '../../src/services/theme';

const API = API_BASE_URL;

interface SleepStage { name: string; minutes: number; percentage: number; }
interface Analysis {
  score: number; grade: string; consistency_score: number;
  avg_duration_hours: number; avg_efficiency: number;
  deep_sleep_pct: number; rem_sleep_pct: number;
  consistency_trend: string; recommendations: string[];
  stage_breakdown: SleepStage[];
}

interface SleepLog {
  id: string; date: string; total_minutes: number; efficiency_pct: number; logged_at: string;
}

const STAGE_COLORS: Record<string, string> = {
  awake: '#EF4444', light: '#818CF8', deep: '#4F46E5', rem: '#22C55E',
};

const GRADE_COLORS: Record<string, string> = {
  A: '#22C55E', B: '#818CF8', C: '#EAB308', D: '#F97316', F: '#EF4444',
};

export default function SleepScreen() {
  const userId = useUserStore((s) => s.userId);
  const { theme } = useTheme();
  const s = makeStyles(theme);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [logs, setLogs] = useState<SleepLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchData(); }, []);

  async function fetchData() {
    setLoading(true);
    try {
      const [aRes, lRes] = await Promise.all([
        fetch(`${API}/api/v1/sleep/analysis?user_id=${userId}&days=7`),
        fetch(`${API}/api/v1/sleep/logs?user_id=${userId}&days=7`),
      ]);
      if (aRes.ok) setAnalysis(await aRes.json());
      if (lRes.ok) setLogs(await lRes.json());
    } catch {}
    setLoading(false);
  }

  async function quickLog() {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    try {
      const res = await fetch(`${API}/api/v1/sleep/logs?user_id=${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bedtime: '23:00', wake_time: '07:00', total_minutes: 480,
          efficiency_pct: 90, deep_pct: 20, rem_pct: 22, light_pct: 45, awake_pct: 13,
        }),
      });
      if (res.ok) fetchData();
    } catch {}
  }

  async function deleteLog(id: string) {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    try {
      const res = await fetch(`${API}/api/v1/sleep/logs/${id}?user_id=${userId}`, { method: 'DELETE' });
      if (res.ok) fetchData();
    } catch {}
  }

  function ScoreRing({ score, color }: { score: number; color: string }) {
    const r = 54;
    const circ = 2 * Math.PI * r;
    const offset = circ - (score / 100) * circ;
    return (
      <View style={{ width: 140, height: 140 }}>
        <Svg width={140} height={140} viewBox="0 0 140 140">
          <Circle cx={70} cy={70} r={r} stroke={theme.border} strokeWidth={10} fill="none" />
          <Circle cx={70} cy={70} r={r} stroke={color} strokeWidth={10} fill="none"
            strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
            transform="rotate(-90 70 70)" />
        </Svg>
        <View style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, alignItems: 'center', justifyContent: 'center' }}>
          <Text style={{ fontSize: 36, fontWeight: '800', color }}>{score}</Text>
          <Text style={{ fontSize: 12, color: theme.textMuted }}>/ 100</Text>
        </View>
      </View>
    );
  }

  if (loading) return <LoadingScreen />;

  const gradeColor = analysis ? GRADE_COLORS[analysis.grade] || theme.textMuted : theme.textMuted;
  const TrendIcon = analysis?.consistency_trend === 'improving' ? TrendingUp
    : analysis?.consistency_trend === 'declining' ? TrendingDown : Minus;

  return (
    <ScrollView style={s.container} contentContainerStyle={{ paddingBottom: 100 }}>
      <Text style={s.title} accessibilityRole="header">Sleep</Text>
      <Text style={s.subtitle}>Rest and recovery analysis</Text>

      {analysis && analysis.score > 0 ? (
        <>
          <View style={s.scoreSection}>
            <ScoreRing score={analysis.score} color={gradeColor} />
            <View style={s.scoreInfo}>
              <Text style={[s.grade, { color: gradeColor }]}>Grade {analysis.grade}</Text>
              <Text style={s.metric}>Duration: {analysis.avg_duration_hours}h</Text>
              <Text style={s.metric}>Efficiency: {analysis.avg_efficiency}%</Text>
              <View style={s.trendRow}>
                <TrendIcon size={14} color={gradeColor} />
                <Text style={[s.metric, { color: gradeColor }]}>{analysis.consistency_trend}</Text>
              </View>
            </View>
          </View>

          <Text style={s.sectionTitle}>Sleep Stages</Text>
          <View style={s.stagesCard}>
            {analysis.stage_breakdown.map((st) => (
              <View key={st.name} style={s.stageRow}>
                <View style={[s.stageDot, { backgroundColor: STAGE_COLORS[st.name] }]} />
                <Text style={s.stageName}>{st.name}</Text>
                <View style={s.stageBarBg}>
                  <View style={[s.stageBarFill, { width: `${st.percentage}%`, backgroundColor: STAGE_COLORS[st.name] }]} />
                </View>
                <Text style={s.stagePct}>{st.percentage}%</Text>
                <Text style={s.stageMin}>{st.minutes}m</Text>
              </View>
            ))}
          </View>

          <Text style={s.sectionTitle}>Recommendations</Text>
          {analysis.recommendations.map((r, i) => (
            <View key={i} style={s.recCard}>
              <Moon size={14} color={theme.primaryLight} />
              <Text style={s.recText}>{r}</Text>
            </View>
          ))}
        </>
      ) : (
        <View style={s.empty}>
          <Moon size={40} color={theme.border} />
          <Text style={s.emptyTitle}>No Sleep Data</Text>
          <Text style={s.emptyDesc}>Log your sleep to see analysis and recommendations.</Text>
        </View>
      )}

      <TouchableOpacity style={s.addBtn} onPress={quickLog}>
        <Plus size={16} color="#fff" />
        <Text style={s.addBtnText}>Log Sleep</Text>
      </TouchableOpacity>

      <Text style={s.sectionTitle}>Recent Logs</Text>
      {logs.map((l) => (
        <View key={l.id} style={s.logCard}>
          <View style={s.logInfo}>
            <Text style={s.logDate}>{l.date}</Text>
            <Text style={s.logDetail}>{Math.floor(l.total_minutes / 60)}h {l.total_minutes % 60}m · {l.efficiency_pct}% efficiency</Text>
          </View>
          <TouchableOpacity onPress={() => deleteLog(l.id)}>
            <Trash2 size={14} color={theme.danger} />
          </TouchableOpacity>
        </View>
      ))}
    </ScrollView>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.background, padding: 20 },
    title: { fontSize: 28, fontWeight: '700', color: theme.text, marginTop: 48 },
    subtitle: { fontSize: 14, color: theme.textMuted, marginBottom: 16 },
    scoreSection: { flexDirection: 'row', backgroundColor: theme.surface, borderRadius: 16, padding: 20, marginBottom: 16, alignItems: 'center' },
    scoreInfo: { flex: 1, marginLeft: 16 },
    grade: { fontSize: 20, fontWeight: '700', marginBottom: 4 },
    metric: { fontSize: 14, color: theme.textSecondary, marginBottom: 2 },
    trendRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 4 },
    sectionTitle: { fontSize: 16, fontWeight: '600', color: theme.text, marginTop: 16, marginBottom: 8 },
    stagesCard: { backgroundColor: theme.surface, borderRadius: 12, padding: 14 },
    stageRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
    stageDot: { width: 8, height: 8, borderRadius: 4, marginRight: 8 },
    stageName: { fontSize: 13, color: theme.textSecondary, width: 50 },
    stageBarBg: { flex: 1, height: 6, backgroundColor: theme.surfaceHover, borderRadius: 3, marginHorizontal: 8 },
    stageBarFill: { height: 6, borderRadius: 3 },
    stagePct: { fontSize: 12, color: theme.textSecondary, width: 35, textAlign: 'right' },
    stageMin: { fontSize: 11, color: theme.textMuted, width: 30, textAlign: 'right' },
    recCard: {
      flexDirection: 'row', alignItems: 'flex-start', gap: 10,
      backgroundColor: theme.surface, borderRadius: 12, padding: 12, marginBottom: 8,
    },
    recText: { flex: 1, fontSize: 13, color: theme.textSecondary, lineHeight: 18 },
    addBtn: {
      flexDirection: 'row', alignItems: 'center', gap: 8,
      backgroundColor: theme.primary, borderRadius: 12, padding: 12, marginVertical: 12,
    },
    addBtnText: { color: '#fff', fontSize: 14, fontWeight: '600' },
    logCard: {
      flexDirection: 'row', alignItems: 'center', backgroundColor: theme.surface,
      borderRadius: 12, padding: 12, marginBottom: 8,
    },
    logInfo: { flex: 1 },
    logDate: { fontSize: 14, fontWeight: '600', color: theme.text },
    logDetail: { fontSize: 12, color: theme.textMuted, marginTop: 2 },
    empty: { alignItems: 'center', padding: 40 },
    emptyTitle: { fontSize: 18, fontWeight: '600', color: theme.text, marginTop: 12 },
    emptyDesc: { fontSize: 14, color: theme.textMuted, marginTop: 4, textAlign: 'center' },
  });
}
