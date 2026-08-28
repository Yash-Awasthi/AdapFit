import React from 'react';
import { View, Text, Image, StyleSheet } from 'react-native';
import { useTheme } from '../services/theme';

interface Exercise {
  name: string;
  target_muscle: string;
  sets: number;
  target_reps: string;
  target_rpe?: number;
  gif_url?: string;
}

interface Props {
  exercise: Exercise;
}

export function WorkoutCard({ exercise }: Props) {
  const { theme } = useTheme();
  return (
    <View style={[styles.card, { backgroundColor: theme.surface }]}>
      {exercise.gif_url ? (
        <Image source={{ uri: exercise.gif_url }} style={styles.image} />
      ) : (
        <View style={[styles.image, styles.placeholder, { backgroundColor: theme.surfaceHover }]}>
          <Text style={[styles.placeholderText, { color: theme.primaryLight }]}>{exercise.name.charAt(0)}</Text>
        </View>
      )}
      <View style={styles.info}>
        <Text style={[styles.name, { color: theme.text }]}>{exercise.name}</Text>
        <Text style={[styles.muscle, { color: theme.textSecondary }]}>{exercise.target_muscle}</Text>
        <Text style={[styles.detail, { color: theme.textMuted }]}>
          {exercise.sets} sets x {exercise.target_reps}
        </Text>
      </View>
      {exercise.target_rpe && (
        <View style={[styles.rpeBadge, { backgroundColor: theme.primaryBg }]}>
          <Text style={[styles.rpeText, { color: theme.primaryLight }]}>RPE {exercise.target_rpe}</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    flexDirection: 'row',
    alignItems: 'center',
  },
  image: {
    width: 64,
    height: 64,
    borderRadius: 8,
    marginRight: 12,
  },
  placeholder: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  placeholderText: {
    fontSize: 24,
    fontWeight: '700',
  },
  info: {
    flex: 1,
  },
  name: {
    fontSize: 16,
    fontWeight: '600',
  },
  muscle: {
    fontSize: 13,
    marginTop: 2,
  },
  detail: {
    fontSize: 13,
    marginTop: 4,
  },
  rpeBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  rpeText: {
    fontSize: 12,
    fontWeight: '600',
  },
});
