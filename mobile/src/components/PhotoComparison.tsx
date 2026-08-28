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
    <View style={styles.container}>
      <Text style={styles.title}>Progress Photos</Text>

      {/* Photo Comparison */}
      <View style={styles.photoContainer} {...panResponder.panHandlers}>
        {/* Before Photo (left side) */}
        <View style={[styles.photoSide, { width: sliderPosition }]}>
          {beforeUri ? (
            <Image source={{ uri: beforeUri }} style={styles.photo} />
          ) : (
            <View style={[styles.photo, styles.placeholder]}>
              <Text style={styles.placeholderText}>Before</Text>
            </View>
          )}
          <View style={styles.dateBadge}>
            <Calendar size={10} color="#F8FAFC" />
            <Text style={styles.dateText}>{beforeDate}</Text>
          </View>
        </View>

        {/* After Photo (right side) */}
        <View style={[styles.photoSide, styles.photoRight, { width: SCREEN_WIDTH - sliderPosition }]}>
          {afterUri ? (
            <Image source={{ uri: afterUri }} style={styles.photo} />
          ) : (
            <View style={[styles.photo, styles.placeholder, { backgroundColor: '#1E3A1E' }]}>
              <Text style={styles.placeholderText}>After</Text>
            </View>
          )}
          <View style={styles.dateBadge}>
            <Calendar size={10} color="#F8FAFC" />
            <Text style={styles.dateText}>{afterDate}</Text>
          </View>
        </View>

        {/* Slider Handle */}
        <View style={[styles.slider, { left: sliderPosition - 2 }]}>
          <View style={styles.sliderLine} />
          <View style={styles.sliderHandle}>
            <Text style={styles.sliderIcon}>{'<'}</Text>
            <Text style={styles.sliderIcon}>{'>'}</Text>
          </View>
        </View>
      </View>

      {/* Stats Comparison */}
      <View style={styles.statsRow}>
        {weightDelta !== null && (
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>Weight</Text>
            <View style={styles.statComparison}>
              <Text style={styles.statBefore}>{beforeWeight}kg</Text>
              <Text style={styles.statArrow}>→</Text>
              <Text style={styles.statAfter}>{afterWeight}kg</Text>
            </View>
            <Text
              style={[
                styles.statDelta,
                { color: weightDelta <= 0 ? '#22C55E' : '#EF4444' },
              ]}
            >
              {weightDelta > 0 ? '+' : ''}{weightDelta.toFixed(1)}kg
            </Text>
          </View>
        )}

        {bodyFatDelta !== null && (
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>Body Fat</Text>
            <View style={styles.statComparison}>
              <Text style={styles.statBefore}>{beforeBodyFat}%</Text>
              <Text style={styles.statArrow}>→</Text>
              <Text style={styles.statAfter}>{afterBodyFat}%</Text>
            </View>
            <Text
              style={[
                styles.statDelta,
                { color: bodyFatDelta <= 0 ? '#22C55E' : '#EF4444' },
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
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
  },
  title: {
    fontSize: 14,
    fontWeight: '600',
    color: '#F8FAFC',
    marginBottom: 12,
  },
  photoContainer: {
    width: SCREEN_WIDTH,
    height: 240,
    borderRadius: 12,
    overflow: 'hidden',
    position: 'relative',
    backgroundColor: '#0F172A',
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
    backgroundColor: '#334155',
    alignItems: 'center',
    justifyContent: 'center',
  },
  placeholderText: {
    fontSize: 14,
    color: '#8B96AB',
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
    color: '#F8FAFC',
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
    backgroundColor: '#F8FAFC',
    marginLeft: 1,
  },
  sliderHandle: {
    position: 'absolute',
    top: '50%',
    left: -14,
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#F8FAFC',
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 2,
  },
  sliderIcon: {
    fontSize: 10,
    color: '#0F172A',
    fontWeight: '700',
  },
  statsRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 12,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#0F172A',
    borderRadius: 8,
    padding: 10,
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 11,
    color: '#8B96AB',
    marginBottom: 4,
  },
  statComparison: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statBefore: {
    fontSize: 13,
    color: '#94A3B8',
    fontWeight: '500',
  },
  statArrow: {
    fontSize: 12,
    color: '#8B96AB',
  },
  statAfter: {
    fontSize: 13,
    color: '#F8FAFC',
    fontWeight: '700',
  },
  statDelta: {
    fontSize: 12,
    fontWeight: '700',
    marginTop: 4,
  },
});
