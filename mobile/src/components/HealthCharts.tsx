/**
 * HealthCharts — Interactive Data Visualization Library
 * Line charts, bar charts, radar charts, heatmaps, sparklines,
 * progress rings, trend indicators, and metric cards.
 */
import React, { useRef, useEffect } from 'react';
import { View, Text, Animated, Dimensions, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography } from '../theme';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// ─── Mini Line Chart ──────────────────────────────────────────
export function MiniLineChart({ data, color, height = 60, width = 200 }: {
  data: number[]; color: string; height?: number; width?: number;
}) {
  const anim = useRef(new Animated.Value(0)).current;
  useEffect(() => { Animated.timing(anim, { toValue: 1, duration: 800, useNativeDriver: false }).start(); }, []);

  if (!data.length) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  return (
    <View style={{ width, height, justifyContent: 'flex-end' }}>
      {/* Background grid lines */}
      {[0.25, 0.5, 0.75].map(p => (
        <View key={p} style={{ position: 'absolute', bottom: p * height, left: 0, right: 0, height: 0.5, backgroundColor: colors.surface.border + '40' }} />
      ))}
      {/* Simple polyline using positioned dots */}
      <View style={{ flexDirection: 'row', alignItems: 'flex-end', height, gap: 0 }}>
        {data.map((val, i) => {
          const barHeight = ((val - min) / range) * (height - 8) + 4;
          return (
            <Animated.View
              key={i}
              style={{
                flex: 1,
                height: anim.interpolate({ inputRange: [0, 1], outputRange: [0, barHeight] }),
                backgroundColor: i === data.length - 1 ? color : color + '60',
                borderRadius: 2,
                marginHorizontal: 1,
              }}
            />
          );
        })}
      </View>
    </View>
  );
}

// ─── Bar Chart ────────────────────────────────────────────────
export function BarChart({ data, labels, colors: barColors, height = 120, showValues = true }: {
  data: { value: number; label: string; color?: string }[];
  labels?: string[];
  colors?: string[];
  height?: number;
  showValues?: boolean;
}) {
  const anim = useRef(new Animated.Value(0)).current;
  useEffect(() => { Animated.timing(anim, { toValue: 1, duration: 600, useNativeDriver: false }).start(); }, []);

  if (!data.length) return null;
  const max = Math.max(...data.map(d => d.value));

  return (
    <View>
      <View style={{ flexDirection: 'row', alignItems: 'flex-end', height, gap: 4 }}>
        {data.map((item, i) => {
          const barHeight = (item.value / max) * (height - 24);                const barColor = item.color || '#6366F1';
          return (
            <View key={i} style={{ flex: 1, alignItems: 'center' }}>
              {showValues && (
                <Text style={[typography.body.xs, { color: colors.text.muted, marginBottom: 4 }]}>{item.value}</Text>
              )}
              <Animated.View style={{
                width: '80%',
                height: anim.interpolate({ inputRange: [0, 1], outputRange: [0, barHeight] }),
                backgroundColor: barColor,
                borderRadius: 6,
              }} />
              <Text style={[typography.body.xs, { color: colors.text.muted, marginTop: 4 }]} numberOfLines={1}>{item.label}</Text>
            </View>
          );
        })}
      </View>
    </View>
  );
}

// ─── Radar Chart (Simplified) ─────────────────────────────────
export function RadarChart({ data, size = 200 }: {
  data: { label: string; value: number; color?: string }[]; size?: number;
}) {
  const center = size / 2;
  const radius = size / 2 - 20;
  const levels = 4;

  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      {/* Concentric circles */}
      {Array.from({ length: levels }).map((_, i) => (
        <View key={i} style={{
          position: 'absolute',
          width: (radius * 2 * (i + 1)) / levels,
          height: (radius * 2 * (i + 1)) / levels,
          borderRadius: (radius * (i + 1)) / levels,
          borderWidth: 0.5,
          borderColor: colors.surface.border + '40',
        }} />
      ))}
      {/* Labels */}
      {data.map((item, i) => {
        const angle = (Math.PI * 2 * i) / data.length - Math.PI / 2;
        const x = center + (radius + 16) * Math.cos(angle);
        const y = center + (radius + 16) * Math.sin(angle);
        return (
          <Text key={i} style={[typography.body.xs, {
            position: 'absolute',
            left: x - 20,
            top: y - 8,
            width: 40,
            textAlign: 'center',
            color: item.color || colors.text.muted,
          }]} numberOfLines={1}>{item.label}</Text>
        );
      })}
      {/* Data points */}
      {data.map((item, i) => {
        const angle = (Math.PI * 2 * i) / data.length - Math.PI / 2;
        const r = (item.value / 100) * radius;
        const x = center + r * Math.cos(angle);
        const y = center + r * Math.sin(angle);
        return (
          <View key={i} style={{
            position: 'absolute',
            left: x - 4,
            top: y - 4,
            width: 8,
            height: 8,
            borderRadius: 4,
            backgroundColor: item.color || colors.primary,
          }} />
        );
      })}
    </View>
  );
}

// ─── Heatmap (Weekly Calendar) ────────────────────────────────
export function WeeklyHeatmap({ data, labels }: {
  data: number[][]; // [week][day] — values 0-4
  labels?: string[];
}) {
  const dayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const intensityColors = [colors.surface.border + '20', colors.health.success + '30', colors.health.success + '50', colors.health.success + '70', colors.health.success];

  return (
    <View>
      <View style={{ flexDirection: 'row', marginBottom: 4 }}>
        <View style={{ width: 30 }} />
        {dayLabels.map((d, i) => (
          <Text key={i} style={[typography.body.xs, { flex: 1, textAlign: 'center', color: colors.text.muted }]}>{d}</Text>
        ))}
      </View>
      {data.map((week, wi) => (
        <View key={wi} style={{ flexDirection: 'row', marginBottom: 2 }}>
          <Text style={[typography.body.xs, { width: 30, color: colors.text.muted, textAlign: 'right', marginRight: 4 }]}>{labels?.[wi] || `W${wi + 1}`}</Text>
          {week.map((val, di) => (
            <View key={di} style={{
              flex: 1, height: 20, margin: 1, borderRadius: 4,
              backgroundColor: intensityColors[Math.min(val, 4)],
            }} />
          ))}
        </View>
      ))}
    </View>
  );
}

// ─── Sparkline ────────────────────────────────────────────────
export function Sparkline({ data, color, width = 80, height = 24 }: {
  data: number[]; color: string; width?: number; height?: number;
}) {
  if (!data.length) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  return (
    <View style={{ width, height, justifyContent: 'flex-end' }}>
      <View style={{ flexDirection: 'row', alignItems: 'flex-end', height }}>
        {data.map((val, i) => {
          const h = ((val - min) / range) * (height - 4) + 2;
          return (
            <View key={i} style={{ flex: 1, height: h, backgroundColor: color + (i === data.length - 1 ? '' : '60'), borderRadius: 1 }} />
          );
        })}
      </View>
    </View>
  );
}

// ─── Progress Ring ────────────────────────────────────────────
export function ProgressRing({ progress, size = 80, strokeWidth = 6, color, label, value }: {
  progress: number; size?: number; strokeWidth?: number; color: string; label?: string; value?: string;
}) {
  const anim = useRef(new Animated.Value(0)).current;
  useEffect(() => { Animated.timing(anim, { toValue: 1, duration: 800, useNativeDriver: false }).start(); }, []);

  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      <View style={{
        width: size, height: size, borderRadius: size / 2,
        borderWidth: strokeWidth, borderColor: color + '20',
      }} />
      <Animated.View style={{
        position: 'absolute', width: size, height: size, borderRadius: size / 2,
        borderWidth: strokeWidth, borderColor: color,
        transform: [{ rotate: '-90deg' }],
        opacity: anim.interpolate({ inputRange: [0, 1], outputRange: [0, progress / 100] }),
      }} />
      <View style={{ position: 'absolute', alignItems: 'center' }}>
        {value && <Text style={[typography.metric.small, { color: colors.text.primary }]}>{value}</Text>}
        {label && <Text style={[typography.body.xs, { color: colors.text.muted }]}>{label}</Text>}
      </View>
    </View>
  );
}

// ─── Trend Indicator ──────────────────────────────────────────
export function TrendIndicator({ value, direction, color }: {
  value: string; direction: 'up' | 'down' | 'flat'; color: string;
}) {
  const icon = direction === 'up' ? 'trending-up' : direction === 'down' ? 'trending-down' : 'remove';
  const dirColor = direction === 'up' ? colors.health.success : direction === 'down' ? colors.health.danger : colors.text.muted;
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
      <Ionicons name={icon as any} size={14} color={dirColor} />
      <Text style={[typography.body.sm, { color: dirColor }]}>{value}</Text>
    </View>
  );
}

// ─── Metric Card with Sparkline ───────────────────────────────
export function MetricCardWithChart({ title, value, unit, trend, trendDirection, sparkData, color, icon }: {
  title: string; value: string | number; unit?: string;
  trend?: string; trendDirection?: 'up' | 'down' | 'flat';
  sparkData?: number[]; color: string; icon?: string;
}) {
  return (
    <View style={styles.metricCardChart}>
      <View style={styles.metricCardHeader}>
        {icon && (
          <View style={[styles.metricCardIcon, { backgroundColor: color + '18' }]}>
            <Ionicons name={icon as any} size={16} color={color} />
          </View>
        )}
        <Text style={[typography.body.sm, { color: colors.text.muted, flex: 1 }]}>{title}</Text>
        {trend && trendDirection && <TrendIndicator value={trend} direction={trendDirection} color={color} />}
      </View>
      <View style={styles.metricCardBody}>
        <View>
          <Text style={[typography.metric.medium, { color: colors.text.primary }]}>{value}</Text>
          {unit && <Text style={[typography.body.sm, { color: colors.text.muted }]}>{unit}</Text>}
        </View>
        {sparkData && <MiniLineChart data={sparkData} color={color} height={40} width={100} />}
      </View>
    </View>
  );
}

// ─── Donut Chart ──────────────────────────────────────────────
export function DonutChart({ segments, size = 120, strokeWidth = 12, centerLabel }: {
  segments: { value: number; color: string; label?: string }[];
  size?: number; strokeWidth?: number;
  centerLabel?: { value: string; sublabel?: string };
}) {
  const total = segments.reduce((sum, s) => sum + s.value, 0);
  let cumulative = 0;

  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      {segments.map((seg, i) => {
        const startAngle = (cumulative / total) * 360;
        cumulative += seg.value;
        const segmentAngle = (seg.value / total) * 360;
        // Simplified: use opacity layers
        return (
          <View key={i} style={{
            position: 'absolute',
            width: size, height: size, borderRadius: size / 2,
            borderWidth: strokeWidth,
            borderColor: seg.color,
            opacity: segmentAngle / 360,
            transform: [{ rotate: `${startAngle}deg` }],
          }} />
        );
      })}
      <View style={{
        width: size - strokeWidth * 2 - 4, height: size - strokeWidth * 2 - 4,
        borderRadius: (size - strokeWidth * 2) / 2,
        backgroundColor: colors.bg.card, alignItems: 'center', justifyContent: 'center',
      }}>
        {centerLabel && (
          <>
            <Text style={[typography.metric.small, { color: colors.text.primary }]}>{centerLabel.value}</Text>
            {centerLabel.sublabel && <Text style={[typography.body.xs, { color: colors.text.muted }]}>{centerLabel.sublabel}</Text>}
          </>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  metricCardChart: {
    backgroundColor: colors.bg.card, borderRadius: 16, padding: 14,
    borderWidth: 1, borderColor: colors.surface.border,
  },
  metricCardHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
  metricCardIcon: {
    width: 28, height: 28, borderRadius: 8,
    justifyContent: 'center', alignItems: 'center',
  },
  metricCardBody: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end' },
});
