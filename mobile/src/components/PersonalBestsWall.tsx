import React, { useEffect, useState } from "react";
import { View, Text, StyleSheet, ScrollView } from "react-native";
import { Trophy, Flame, TrendingUp } from "lucide-react-native";

const API = "http://localhost:8000";

interface PRRecord {
  exercise_id: string;
  exercise_name: string;
  weight_kg: number;
  reps: number;
  estimated_1rm: number;
  date: string;
}

export default function PersonalBestsWall({ userId = "default" }: { userId?: string }) {
  const [prs, setPrs] = useState<Record<string, PRRecord>>({});
  const [totalRecords, setTotalRecords] = useState(0);

  useEffect(() => {
    fetch(`${API}/api/v1/personal-bests?user_id=${userId}`)
      .then((r) => r.json())
      .then((d) => {
        setPrs(d.bests || {});
        setTotalRecords(d.total_records || 0);
      })
      .catch(() => {});
  }, [userId]);

  const exercises = Object.entries(prs);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Trophy size={20} color="#FBBF24" />
        <Text style={styles.title}>Personal Bests</Text>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>{totalRecords}</Text>
        </View>
      </View>

      {exercises.length === 0 ? (
        <View style={styles.empty}>
          <Flame size={32} color="#475569" />
          <Text style={styles.emptyText}>No PRs logged yet</Text>
          <Text style={styles.emptySubtext}>Complete workouts to track your progress</Text>
        </View>
      ) : (
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.scroll}>
          {exercises.map(([id, pr]) => (
            <View key={id} style={styles.card}>
              <Text style={styles.exerciseName} numberOfLines={1}>
                {pr.exercise_name}
              </Text>
              <Text style={styles.weight}>{pr.weight_kg} kg</Text>
              <Text style={styles.detail}>
                {pr.reps} reps | 1RM: {pr.estimated_1rm} kg
              </Text>
              <View style={styles.dateRow}>
                <TrendingUp size={12} color="#10B981" />
                <Text style={styles.date}>{pr.date}</Text>
              </View>
            </View>
          ))}
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, backgroundColor: "#1E293B", borderRadius: 12, marginBottom: 12 },
  header: { flexDirection: "row", alignItems: "center", marginBottom: 12, gap: 8 },
  title: { color: "#F8FAFC", fontSize: 16, fontWeight: "600", flex: 1 },
  badge: { backgroundColor: "#FBBF24", borderRadius: 10, paddingHorizontal: 8, paddingVertical: 2 },
  badgeText: { color: "#0F172A", fontSize: 12, fontWeight: "700" },
  empty: { alignItems: "center", padding: 20 },
  emptyText: { color: "#94A3B8", fontSize: 14, marginTop: 8 },
  emptySubtext: { color: "#64748B", fontSize: 12, marginTop: 4 },
  scroll: { marginHorizontal: -4 },
  card: {
    backgroundColor: "#334155",
    borderRadius: 10,
    padding: 12,
    marginRight: 10,
    minWidth: 140,
  },
  exerciseName: { color: "#CBD5E1", fontSize: 12, marginBottom: 4 },
  weight: { color: "#F8FAFC", fontSize: 22, fontWeight: "700" },
  detail: { color: "#94A3B8", fontSize: 11, marginTop: 2 },
  dateRow: { flexDirection: "row", alignItems: "center", marginTop: 6, gap: 4 },
  date: { color: "#10B981", fontSize: 11 },
});
