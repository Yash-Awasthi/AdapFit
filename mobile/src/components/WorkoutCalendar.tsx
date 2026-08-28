import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useTheme } from '../services/theme';

const DAYS = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];

interface Props {
  workoutDays: string[]; // ISO date strings
  onDayPress?: (date: string) => void;
}

export function WorkoutCalendar({ workoutDays, onDayPress }: Props) {
  const { theme } = useTheme();
  const today = new Date();
  const year = today.getFullYear();
  const month = today.getMonth();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDay = new Date(year, month, 1).getDay();
  const monthName = today.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

  const workoutSet = new Set(workoutDays.map(d => d.slice(0, 10)));
  const cells: (number | null)[] = [];
  for (let i = 0; i < firstDay; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);

  return (
    <View style={[styles.container, { backgroundColor: theme.surface }]}>
      <Text style={[styles.monthTitle, { color: theme.text }]}>{monthName}</Text>
      <View style={styles.headerRow}>
        {DAYS.map((d, i) => (
          <Text key={i} style={[styles.dayLabel, { color: theme.textMuted }]}>{d}</Text>
        ))}
      </View>
      <View style={styles.grid}>
        {cells.map((day, i) => {
          if (day === null) return <View key={`e${i}`} style={styles.cell} />;
          const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
          const hasWorkout = workoutSet.has(dateStr);
          const isToday = day === today.getDate();
          return (
            <TouchableOpacity
              key={`d${i}`}
              style={[
                styles.cell,
                hasWorkout && { backgroundColor: `${theme.success}33` },
                isToday && { borderWidth: 1.5, borderColor: theme.primaryLight },
              ]}
              onPress={() => onDayPress?.(dateStr)}
              activeOpacity={0.7}
            >
              <Text
                style={[
                  styles.cellText,
                  { color: theme.textSecondary },
                  hasWorkout && { color: theme.success, fontWeight: '600' },
                  isToday && { color: theme.primaryLight, fontWeight: '700' },
                ]}
              >
                {day}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 16, padding: 16, marginBottom: 16,
  },
  monthTitle: { fontSize: 16, fontWeight: '600', marginBottom: 12, textAlign: 'center' },
  headerRow: { flexDirection: 'row', marginBottom: 8 },
  dayLabel: { flex: 1, textAlign: 'center', fontSize: 12, fontWeight: '600' },
  grid: { flexDirection: 'row', flexWrap: 'wrap' },
  cell: {
    width: '14.28%', aspectRatio: 1, alignItems: 'center', justifyContent: 'center',
    borderRadius: 8,
  },
  cellText: { fontSize: 13 },
});
