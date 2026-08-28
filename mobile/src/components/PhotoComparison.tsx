/**
 * Body Composition Photo Comparison — side-by-side slider
 * for visualizing physique changes over time.
 */

import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  Image,
  PanResponder,
  StyleSheet,
  Dimensions,
} from 'react-native';
import { Calendar } from 'lucide-react-native';
import { useTheme } from '../services/theme';

interface PhotoComparisonProps {
  beforeUri?: string;
  afterUri?: string;
  beforeDate?: string;
  afterDate?: string;
  beforeWeight?: number;
  afterWeight?: number;
  beforeBodyFat?: number;
  afterBodyFat?: number;
}

const SCREEN_WIDTH = Dimensions.get('window').width - 40;

export function PhotoComparison({
  beforeUri,
  afterUri,
  beforeDate = 'Jan 1',
  afterDate = 'Aug 28',
  beforeWeight,
  afterWeight,
  beforeBodyFat,
  afterBodyFat,
}: PhotoComparisonProps) {
  const { theme } = useTheme();
  const [sliderPosition, setSliderPosition] = useState(SCREEN_WIDTH / 2);
  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: () => true,
      onPanResponderMove: (_, gestureState) => {
        const newX = Math.max(0, Math.min(SCREEN_WIDTH, sliderPosition + gestureState.dx));
        setSliderPosition(newX);
      },
      onPanResponderRelease: () => {},
    })
  ).current;

  const weightDelta = beforeWeight && afterWeight ? afterWeight - beforeWeight : null;
  const bodyFatDelta = beforeBodyFat && afterBodyFat ? afterBodyFat - beforeBodyFat : null;

  return (
    <View style={[styles.container, { backgroundColor: theme.surface }]}>
      <Text style={[styles.title, { color: theme.text }]}>Progress Photos</Text>

      {/* Photo Comparison */}
      <View style={[styles.photoContainer, { backgroundColor: theme.background }]} {...panResponder.panHandlers}>
        {/* Before Photo (left side) */}
        <View style={[styles.photoSide, { width: sliderPosition }]}>
          {beforeUri ? (
            <Image source={{ uri: beforeUri }} style={styles.photo} />
          ) : (
            <View style={[styles.photo, styles.placeholder, { backgroundColor: theme.border }]}>
              <Text style={[styles.placeholderText, { color: theme.textMuted }]}>Before</Text>
            </View>
          )}
          <View style={styles.dateBadge}>
            <Calendar size={10} color={theme.text} />
            <Text style={[styles.dateText, { color: theme.text }]}>{beforeDate}</Text>
          </View>
        </View>

        {/* After Photo (right side) */}
        <View style={[styles.photoSide, styles.photoRight, { width: SCREEN_WIDTH - sliderPosition }]}>
          {afterUri ? (
            <Image source={{ uri: afterUri }} style={styles.photo} />
          ) : (
            <View style={[styles.photo, styles.placeholder, { backgroundColor: '#1E3A1E' }]}>
              <Text style={[styles.placeholderText, { color: theme.textMuted }]}>After</Text>
            </View>
          )}
          <View style={styles.dateBadge}>
            <Calendar size={10} color={theme.text} />
            <Text style={[styles.dateText, { color: theme.text }]}>{afterDate}</Text>
          </View>
        </View>

        {/* Slider Handle */}
        <View style={[styles.slider, { left: sliderPosition - 2 }]}>
          <View style={[styles.sliderLine, { backgroundColor: theme.text }]} />
          <View style={[styles.sliderHandle, { backgroundColor: theme.text }]}>
            <Text style={[styles.sliderIcon, { color: theme.background }]}>{'<'}</Text>
            <Text style={[styles.sliderIcon, { color: theme.background }]}>{'>'}</Text>
          </View>
        </View>
      </View>

      {/* Stats Comparison */}
      <View style={styles.statsRow}>
        {weightDelta !== null && (
          <View style={[styles.statCard, { backgroundColor: theme.background }]}>
            <Text style={[styles.statLabel, { color: theme.textMuted }]}>Weight</Text>
            <View style={styles.statComparison}>
              <Text style={[styles.statBefore, { color: theme.textSecondary }]}>{beforeWeight}kg</Text>
              <Text style={[styles.statArrow, { color: theme.textMuted }]}>→</Text>
              <Text style={[styles.statAfter, { color: theme.text }]}>{afterWeight}kg</Text>
            </View>
            <Text
              style={[
                styles.statDelta,
                { color: weightDelta <= 0 ? theme.success : theme.danger },
              ]}
            >
              {weightDelta > 0 ? '+' : ''}{weightDelta.toFixed(1)}kg
            </Text>
          </View>
        )}

        {bodyFatDelta !== null && (
          <View style={[styles.statCard, { backgroundColor: theme.background }]}>
            <Text style={[styles.statLabel, { color: theme.textMuted }]}>Body Fat</Text>
            <View style={styles.statComparison}>
              <Text style={[styles.statBefore, { color: theme.textSecondary }]}>{beforeBodyFat}%</Text>
              <Text style={[styles.statArrow, { color: theme.textMuted }]}>→</Text>
              <Text style={[styles.statAfter, { color: theme.text }]}>{afterBodyFat}%</Text>
            </View>
            <Text
              style={[
                styles.statDelta,
                { color: bodyFatDelta <= 0 ? theme.success : theme.danger },
              ]}
            >
              {bodyFatDelta > 0 ? '+' : ''}{bodyFatDelta.toFixed(1)}%
            </Text>
          </View>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
  },
  title: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 12,
  },
  photoContainer: {
    width: SCREEN_WIDTH,
    height: 240,
    borderRadius: 12,
    overflow: 'hidden',
    position: 'relative',
  },
  photoSide: {
    position: 'absolute',
    top: 0,
    left: 0,
    height: 240,
    overflow: 'hidden',
  },
  photoRight: {
    right: 0,
    left: 'auto',
  },
  photo: {
    width: SCREEN_WIDTH,
    height: 240,
    resizeMode: 'cover',
  },
  placeholder: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  placeholderText: {
    fontSize: 14,
    fontWeight: '600',
  },
  dateBadge: {
    position: 'absolute',
    bottom: 8,
    left: 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(15, 23, 42, 0.8)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  dateText: {
    fontSize: 11,
    fontWeight: '500',
  },
  slider: {
    position: 'absolute',
    top: 0,
    width: 4,
    height: 240,
    zIndex: 10,
  },
  sliderLine: {
    flex: 1,
    width: 2,
    marginLeft: 1,
  },
  sliderHandle: {
    position: 'absolute',
    top: '50%',
    left: -14,
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 2,
  },
  sliderIcon: {
    fontSize: 10,
    fontWeight: '700',
  },
  statsRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 12,
  },
  statCard: {
    flex: 1,
    borderRadius: 8,
    padding: 10,
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 11,
    marginBottom: 4,
  },
  statComparison: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statBefore: {
    fontSize: 13,
    fontWeight: '500',
  },
  statArrow: {
    fontSize: 12,
  },
  statAfter: {
    fontSize: 13,
    fontWeight: '700',
  },
  statDelta: {
    fontSize: 12,
    fontWeight: '700',
    marginTop: 4,
  },
});
