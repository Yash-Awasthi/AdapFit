import React from 'react';
import { View, Text, Image, StyleSheet } from 'react-native';

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
  return (
    <View style={styles.card}>
      {exercise.gif_url ? (
        <Image source={{ uri: exercise.gif_url }} style={styles.image} />
      ) : (
        <View style={[styles.image, styles.placeholder]}>
          <Text style={styles.placeholderText}>{exercise.name.charAt(0)}</Text>
        </View>
      )}
      <View style={styles.info}>
        <Text style={styles.name}>{exercise.name}</Text>
        <Text style={styles.muscle}>{exercise.target_muscle}</Text>
        <Text style={styles.detail}>
          {exercise.sets} sets x {exercise.target_reps}
        </Text>
      </View>
      {exercise.target_rpe && (
        <View style={styles.rpeBadge}>
          <Text style={styles.rpeText}>RPE {exercise.target_rpe}</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#1E293B',
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
    backgroundColor: '#334155',
    alignItems: 'center',
    justifyContent: 'center',
  },
  placeholderText: {
    fontSize: 24,
    fontWeight: '700',
    color: '#818CF8',
  },
  info: {
    flex: 1,
  },
  name: {
    fontSize: 16,
    fontWeight: '600',
    color: '#F8FAFC',
  },
  muscle: {
    fontSize: 13,
    color: '#94A3B8',
    marginTop: 2,
  },
  detail: {
    fontSize: 13,
    color: '#8B96AB',
    marginTop: 4,
  },
  rpeBadge: {
    backgroundColor: 'rgba(99, 102, 241, 0.15)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  rpeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#818CF8',
  },
});
