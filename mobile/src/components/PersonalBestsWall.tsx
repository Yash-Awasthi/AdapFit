import React, { useEffect, useState } from "react";
import { View, Text, StyleSheet, ScrollView } from "react-native";
import { Trophy, Flame, TrendingUp } from "lucide-react-native";
import { API_BASE_URL } from "../services/config";
import { useUserStore } from "../stores/userStore";
import { useTheme } from "../services/theme";

interface PRRecord {
  exercise_id: string;
  exercise_name: string;
  weight_kg: number;
  reps: number;
  estimated_1rm: number;
  date: string;
}

export default function PersonalBestsWall({ userId }: { userId?: string }) {
  const { theme } = useTheme();
  const storeUserId = useUserStore((s) => s.userId);
  const resolvedUserId = userId || storeUserId;
  const [prs, setPrs] = useState<Record<string, PRRecord>>({});
  const [totalRecords, setTotalRecords] = useState(0);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/v1/personal-bests?user_id=${resolvedUserId}`)
      .then((r) => r.json())
      .then((d) => {
        setPrs(d.bests || {});
        setTotalRecords(d.total_records || 0);
      })
      .catch(() => {});
  }, [resolvedUserId]);

  const exercises = Object.entries(prs);

  return (
    <View style={[styles.container, { backgroundColor: theme.surface }]}>
      <View style={styles.header}>
        <Trophy size={20} color={theme.warning} />
        <Text style={[styles.title, { color: theme.text }]}>Personal Bests</Text>
        <View style={[styles.badge, { backgroundColor: theme.warning }]}>
          <Text style={styles.badgeText}>{totalRecords}</Text>
        </View>
      </View>

      {exercises.length === 0 ? (
        <View style={styles.empty}>
          <Flame size={32} color={theme.textMuted} />
          <Text style={[styles.emptyText, { color: theme.textSecondary }]}>No PRs logged yet</Text>
          <Text style={[styles.emptySubtext, { color: theme.textMuted }]}>Complete workouts to track your progress</Text>
        </View>
      ) : (
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.scroll}>
          {exercises.map(([id, pr]) => (
            <View key={id} style={[styles.card, { backgroundColor: theme.surfaceHover }]}>
              <Text style={[styles.exerciseName, { color: theme.textSecondary }]} numberOfLines={1}>
                {pr.exercise_name}
              </Text>
              <Text style={[styles.weight, { color: theme.text }]}>{pr.weight_kg} kg</Text>
              <Text style={[styles.detail, { color: theme.textMuted }]}>
                {pr.reps} reps | 1RM: {pr.estimated_1rm} kg
              </Text>
              <View style={styles.dateRow}>
                <TrendingUp size={12} color={theme.success} />
                <Text style={[styles.date, { color: theme.success }]}>{pr.date}</Text>
              </View>
            </View>
          ))}
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, borderRadius: 12, marginBottom: 12 },
  header: { flexDirection: "row", alignItems: "center", marginBottom: 12, gap: 8 },
  title: { fontSize: 16, fontWeight: "600", flex: 1 },
  badge: { borderRadius: 10, paddingHorizontal: 8, paddingVertical: 2 },
  badgeText: { color: "#0F172A", fontSize: 12, fontWeight: "700" },
  empty: { alignItems: "center", padding: 20 },
  emptyText: { fontSize: 14, marginTop: 8 },
  emptySubtext: { fontSize: 12, marginTop: 4 },
  scroll: { marginHorizontal: -4 },
  card: {
    borderRadius: 10,
    padding: 12,
    marginRight: 10,
    minWidth: 140,
  },
  exerciseName: { fontSize: 12, marginBottom: 4 },
  weight: { fontSize: 22, fontWeight: "700" },
  detail: { fontSize: 11, marginTop: 2 },
  dateRow: { flexDirection: "row", alignItems: "center", marginTop: 6, gap: 4 },
  date: { fontSize: 11 },
});
