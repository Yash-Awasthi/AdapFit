import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Circle } from 'react-native-svg';
import { useTheme, CARD_SHADOW } from '../services/theme';

type State = 'OPTIMAL' | 'MODERATE' | 'REDUCED' | 'DEPLETED';

const COLORS: Record<State, string> = {
  OPTIMAL: '#22C55E',
  MODERATE: '#EAB308',
  REDUCED: '#F97316',
  DEPLETED: '#EF4444',
};

const DIRECTIVES: Record<State, string> = {
  OPTIMAL: 'High readiness. Push hard today!',
  MODERATE: 'Standard training permitted.',
  REDUCED: 'Scale back intensity.',
  DEPLETED: 'Rest day recommended.',
};

interface Props {
  score: number;
  state: State;
  directive: string;
  accessibilityLabel?: string;
  accessibilityHint?: string;
}

export function RecoveryCard({ score, state, directive, accessibilityLabel, accessibilityHint }: Props) {
  const { theme } = useTheme();
  const color = COLORS[state] || '#EAB308';
  const circumference = 2 * Math.PI * 54;
  const progress = (score / 100) * circumference;

  return (
    <View
      style={[styles.card, CARD_SHADOW, { backgroundColor: theme.surface, borderColor: theme.border }]}
      accessible
      accessibilityLabel={accessibilityLabel}
      accessibilityHint={accessibilityHint}
    >
      <View style={styles.gaugeContainer}>
        <Svg width={140} height={140} viewBox="0 0 140 140">
          <Circle cx={70} cy={70} r={54} stroke={theme.border} strokeWidth={10} fill="none" />
          <Circle
            cx={70}
            cy={70}
            r={54}
            stroke={color}
            strokeWidth={10}
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={circumference - progress}
            strokeLinecap="round"
            transform="rotate(-90 70 70)"
          />
        </Svg>
        <View style={styles.scoreContainer}>
          <Text style={[styles.score, { color }]}>{score}</Text>
          <Text style={[styles.scoreLabel, { color: theme.textMuted }]}>/ 100</Text>
        </View>
      </View>
      <View style={[styles.badge, { backgroundColor: color + '20' }]}>
        <Text style={[styles.badgeText, { color }]}>{state}</Text>
      </View>
      <Text style={[styles.directive, { color: theme.textSecondary }]}>{directive || DIRECTIVES[state]}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 18,
    borderWidth: 1,
    padding: 20,
    marginBottom: 16,
    alignItems: 'center',
  },
  gaugeContainer: {
    position: 'relative',
    width: 140,
    height: 140,
    marginBottom: 12,
  },
  scoreContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    alignItems: 'center',
    justifyContent: 'center',
  },
  score: {
    fontSize: 40,
    fontWeight: '800',
  },
  scoreLabel: {
    fontSize: 12,
  },
  badge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
    marginBottom: 12,
  },
  badgeText: {
    fontSize: 14,
    fontWeight: '700',
  },
  directive: {
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
  },
});
