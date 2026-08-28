import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

const DAYS = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];

interface Props {
  workoutDays: string[]; // ISO date strings
  onDayPress?: (date: string) => void;
}

export function WorkoutCalendar({ workoutDays, onDayPress }: Props) {
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
    <View style={styles.container}>
      <Text style={styles.monthTitle}>{monthName}</Text>
      <View style={styles.headerRow}>
        {DAYS.map((d, i) => (
          <Text key={i} style={styles.dayLabel}>{d}</Text>
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
              style={[styles.cell, hasWorkout && styles.cellWorkout, isToday && styles.cellToday]}
              onPress={() => onDayPress?.(dateStr)}
              activeOpacity={0.7}
            >
              <Text style={[styles.cellText, hasWorkout && styles.cellTextWorkout, isToday && styles.cellTextToday]}>
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
    backgroundColor: '#1E293B', borderRadius: 16, padding: 16, marginBottom: 16,
  },
  monthTitle: { fontSize: 16, fontWeight: '600', color: '#F8FAFC', marginBottom: 12, textAlign: 'center' },
  headerRow: { flexDirection: 'row', marginBottom: 8 },
  dayLabel: { flex: 1, textAlign: 'center', fontSize: 12, fontWeight: '600', color: '#8B96AB' },
  grid: { flexDirection: 'row', flexWrap: 'wrap' },
  cell: {
    width: '14.28%', aspectRatio: 1, alignItems: 'center', justifyContent: 'center',
    borderRadius: 8,
  },
  cellWorkout: { backgroundColor: 'rgba(34, 197, 94, 0.2)' },
  cellToday: { borderWidth: 1.5, borderColor: '#818CF8' },
  cellText: { fontSize: 13, color: '#94A3B8' },
  cellTextWorkout: { color: '#22C55E', fontWeight: '600' },
  cellTextToday: { color: '#818CF8', fontWeight: '700' },
});
