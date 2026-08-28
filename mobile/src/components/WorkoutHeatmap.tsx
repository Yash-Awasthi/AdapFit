/**
 * GitHub-style contribution heatmap showing workout frequency.
 * Displays 52 weeks of workout data with color-coded intensity.
 */

import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useTheme } from '../services/theme';

interface HeatmapProps {
  workoutDates: string[]; // ISO date strings
  year?: number;
}

interface DayData {
  date: string;
  count: number;
  level: 0 | 1 | 2 | 3 | 4; // intensity levels
}

const INTENSITY_COLORS = ['#1E3A1E', '#22C55E', '#16A34A', '#15803D']; // levels 1-4, empty (0) comes from theme
const LEVEL_LABELS = ['No workout', 'Light', 'Moderate', 'Hard', 'Intense'];
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const DAYS = ['Mon', '', 'Wed', '', 'Fri', '', ''];

function getDaysInYear(year: number): DayData[] {
  const days: DayData[] = [];
  const startDate = new Date(year, 0, 1);
  const endDate = new Date(year, 11, 31);

  for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
    days.push({
      date: d.toISOString().split('T')[0],
      count: 0,
      level: 0,
    });
  }
  return days;
}

function computeLevels(days: DayData[]): DayData[] {
  const maxCount = Math.max(1, ...days.map((d) => d.count));
  return days.map((d) => {
    if (d.count === 0) return { ...d, level: 0 as const };
    const ratio = d.count / maxCount;
    if (ratio <= 0.25) return { ...d, level: 1 as const };
    if (ratio <= 0.5) return { ...d, level: 2 as const };
    if (ratio <= 0.75) return { ...d, level: 3 as const };
    return { ...d, level: 4 as const };
  });
}

export function WorkoutHeatmap({ workoutDates, year = new Date().getFullYear() }: HeatmapProps) {
  const { theme } = useTheme();
  const [selectedDay, setSelectedDay] = useState<DayData | null>(null);
  const levelColors = [theme.surfaceHover, ...INTENSITY_COLORS];

  // Build heatmap data
  const days = getDaysInYear(year);
  const dateCounts = new Map<string, number>();
  for (const date of workoutDates) {
    const d = date.split('T')[0];
    dateCounts.set(d, (dateCounts.get(d) || 0) + 1);
  }
  const enriched = days.map((d) => ({ ...d, count: dateCounts.get(d.date) || 0 }));
  const leveled = computeLevels(enriched);

  // Stats
  const totalWorkouts = workoutDates.length;
  const currentStreak = computeStreak(workoutDates);
  const bestStreak = computeBestStreak(workoutDates);

  // Organize by weeks (7 rows x ~53 columns)
  const weeks: DayData[][] = [];
  let currentWeek: DayData[] = [];

  // Pad start to align with day of week
  const firstDay = new Date(year, 0, 1);
  const startDow = (firstDay.getDay() + 6) % 7; // Monday = 0
  for (let i = 0; i < startDow; i++) {
    currentWeek.push({ date: '', count: 0, level: 0 });
  }

  for (const day of leveled) {
    currentWeek.push(day);
    if (currentWeek.length === 7) {
      weeks.push(currentWeek);
      currentWeek = [];
    }
  }
  if (currentWeek.length > 0) {
    while (currentWeek.length < 7) {
      currentWeek.push({ date: '', count: 0, level: 0 });
    }
    weeks.push(currentWeek);
  }

  // Month labels
  const monthLabels: { month: string; weekIndex: number }[] = [];
  let lastMonth = -1;
  weeks.forEach((week, i) => {
    const firstValid = week.find((d) => d.date);
    if (firstValid) {
      const m = new Date(firstValid.date).getMonth();
      if (m !== lastMonth) {
        monthLabels.push({ month: MONTHS[m], weekIndex: i });
        lastMonth = m;
      }
    }
  });

  return (
    <View style={[styles.container, { backgroundColor: theme.surface }]}>
      {/* Stats Header */}
      <View style={styles.statsRow}>
        <View style={styles.stat}>
          <Text style={[styles.statValue, { color: theme.text }]}>{totalWorkouts}</Text>
          <Text style={[styles.statLabel, { color: theme.textMuted }]}>workouts</Text>
        </View>
        <View style={styles.stat}>
          <Text style={[styles.statValue, { color: theme.warning }]}>{currentStreak}</Text>
          <Text style={[styles.statLabel, { color: theme.textMuted }]}>current streak</Text>
        </View>
        <View style={styles.stat}>
          <Text style={[styles.statValue, { color: theme.success }]}>{bestStreak}</Text>
          <Text style={[styles.statLabel, { color: theme.textMuted }]}>best streak</Text>
        </View>
      </View>

      {/* Month Labels */}
      <View style={styles.monthRow}>
        {monthLabels.map((m, i) => (
          <Text
            key={i}
            style={[styles.monthLabel, { color: theme.textMuted, marginLeft: m.weekIndex === 0 ? 0 : 4 }]}
          >
            {m.month}
          </Text>
        ))}
      </View>

      {/* Heatmap Grid */}
      <View style={styles.grid}>
        {/* Day labels */}
        <View style={styles.dayLabels}>
          {DAYS.map((d, i) => (
            <Text key={i} style={[styles.dayLabel, { color: theme.textMuted }]}>{d}</Text>
          ))}
        </View>

        {/* Week columns */}
        <View style={styles.weeksContainer}>
          {weeks.map((week, wi) => (
            <View key={wi} style={styles.weekColumn}>
              {week.map((day, di) => (
                <TouchableOpacity
                  key={di}
                  style={[
                    styles.dayCell,
                    { backgroundColor: day.date ? levelColors[day.level] : 'transparent' },
                  ]}
                  onPress={() => day.date && setSelectedDay(day)}
                  disabled={!day.date}
                />
              ))}
            </View>
          ))}
        </View>
      </View>

      {/* Legend */}
      <View style={styles.legend}>
        <Text style={[styles.legendLabel, { color: theme.textMuted }]}>Less</Text>
        {levelColors.map((color, i) => (
          <View key={i} style={[styles.legendCell, { backgroundColor: color }]} />
        ))}
        <Text style={[styles.legendLabel, { color: theme.textMuted }]}>More</Text>
      </View>

      {/* Selected Day Tooltip */}
      {selectedDay && selectedDay.date && (
        <View style={[styles.tooltip, { backgroundColor: theme.background }]}>
          <Text style={[styles.tooltipText, { color: theme.textSecondary }]}>
            {selectedDay.date}: {selectedDay.count} workout{selectedDay.count !== 1 ? 's' : ''} — {LEVEL_LABELS[selectedDay.level]}
          </Text>
          <TouchableOpacity onPress={() => setSelectedDay(null)}>
            <Text style={[styles.tooltipClose, { color: theme.textMuted }]}>x</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

function computeStreak(dates: string[]): number {
  if (!dates.length) return 0;
  const sorted = [...new Set(dates.map((d) => d.split('T')[0]))].sort().reverse();
  let streak = 0;
  const today = new Date().toISOString().split('T')[0];

  for (let i = 0; i < sorted.length; i++) {
    const expected = new Date();
    expected.setDate(expected.getDate() - i);
    const expectedStr = expected.toISOString().split('T')[0];
    if (sorted[i] === expectedStr) {
      streak++;
    } else {
      break;
    }
  }
  return streak;
}

function computeBestStreak(dates: string[]): number {
  if (!dates.length) return 0;
  const unique = [...new Set(dates.map((d) => d.split('T')[0]))].sort();
  let best = 1;
  let current = 1;

  for (let i = 1; i < unique.length; i++) {
    const prev = new Date(unique[i - 1]);
    const curr = new Date(unique[i]);
    const diffDays = (curr.getTime() - prev.getTime()) / (1000 * 60 * 60 * 24);
    if (diffDays === 1) {
      current++;
      best = Math.max(best, current);
    } else {
      current = 1;
    }
  }
  return best;
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 12,
    padding: 12,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 12,
  },
  stat: { alignItems: 'center' },
  statValue: { fontSize: 20, fontWeight: '800' },
  statLabel: { fontSize: 11 },
  monthRow: {
    flexDirection: 'row',
    marginBottom: 4,
    marginLeft: 24,
  },
  monthLabel: {
    fontSize: 10,
    width: 30,
  },
  grid: { flexDirection: 'row' },
  dayLabels: { marginRight: 4, justifyContent: 'space-between' },
  dayLabel: { fontSize: 9, height: 12, textAlign: 'right' },
  weeksContainer: { flexDirection: 'row', gap: 2 },
  weekColumn: { gap: 2 },
  dayCell: {
    width: 11,
    height: 11,
    borderRadius: 2,
  },
  legend: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    gap: 4,
    marginTop: 8,
  },
  legendLabel: { fontSize: 9 },
  legendCell: { width: 11, height: 11, borderRadius: 2 },
  tooltip: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderRadius: 8,
    padding: 8,
    marginTop: 8,
  },
  tooltipText: { fontSize: 11, flex: 1 },
  tooltipClose: { fontSize: 14, marginLeft: 8 },
});
