/**
 * Interactive Chart Components — Animated, Touchable, Beautiful
 * Line charts, bar charts, ring charts, sparklines with gesture support
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, Animated,
  Dimensions, PanResponder, Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../theme';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// ===== INTERACTIVE LINE CHART =====
interface LineChartProps {
  data: number[];
  labels?: string[];
  color?: string;
  gradient?: string[];
  height?: number;
  showDots?: boolean;
  showArea?: boolean;
  showGrid?: boolean;
  showLabels?: boolean;
  animated?: boolean;
  onDataPointPress?: (index: number, value: number) => void;
}

export const InteractiveLineChart: React.FC<LineChartProps> = ({
  data,
  labels,
  color = colors.primary,
  gradient,
  height = 200,
  showDots = true,
  showArea = true,
  showGrid = true,
  showLabels = true,
  animated = true,
  onDataPointPress,
}) => {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const animValue = useRef(new Animated.Value(0)).current;
  const chartWidth = SCREEN_WIDTH - spacing.screenPadding * 2 - 40;
  const chartHeight = height - 40;

  useEffect(() => {
    if (animated) {
      Animated.timing(animValue, { toValue: 1, duration: 800, useNativeDriver: false }).start();
    } else {
      animValue.setValue(1);
    }
  }, [data]);

  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const step = chartWidth / Math.max(1, data.length - 1);

  const points = data.map((val, i) => ({
    x: i * step,
    y: chartHeight - ((val - min) / range) * chartHeight,
  }));

  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');

  return (
    <View style={styles.chartContainer}>
      {/* Y-axis labels */}
      {showLabels && (
        <View style={styles.yAxisLabels}>
          <Text style={styles.axisLabel}>{max.toFixed(0)}</Text>
          <Text style={styles.axisLabel}>{((max + min) / 2).toFixed(0)}</Text>
          <Text style={styles.axisLabel}>{min.toFixed(0)}</Text>
        </View>
      )}

      {/* Chart area */}
      <View style={[styles.chartArea, { height: chartHeight, width: chartWidth }]}>
        {/* Grid lines */}
        {showGrid && (
          <View style={styles.gridContainer}>
            {[0, 1, 2, 3, 4].map(i => (
              <View key={i} style={[styles.gridLine, { top: `${(i / 4) * 100}%` }]} />
            ))}
          </View>
        )}

        {/* Data points */}
        {points.map((p, i) => {
          const isSelected = selectedIndex === i;
          return (
            <TouchableOpacity
              key={i}
              style={[
                styles.dataPoint,
                {
                  left: p.x - 12,
                  top: p.y - 12,
                  width: 24,
                  height: 24,
                },
              ]}
              onPress={() => {
                setSelectedIndex(i);
                onDataPointPress?.(i, data[i]);
              }}
              activeOpacity={0.7}
            >
              {showDots && (
                <Animated.View
                  style={[
                    styles.dot,
                    {
                      backgroundColor: color,
                      transform: [{ scale: isSelected ? 1.5 : animValue }],
                      shadowColor: isSelected ? color : 'transparent',
                      shadowOffset: { width: 0, height: 0 },
                      shadowOpacity: isSelected ? 0.5 : 0,
                      shadowRadius: isSelected ? 8 : 0,
                    },
                  ]}
                />
              )}
            </TouchableOpacity>
          );
        })}

        {/* Selected value tooltip */}
        {selectedIndex !== null && points[selectedIndex] && (
          <View
            style={[
              styles.tooltip,
              {
                left: points[selectedIndex].x - 30,
                top: points[selectedIndex].y - 45,
              },
            ]}
          >
            <Text style={styles.tooltipText}>{data[selectedIndex]}</Text>
            <View style={styles.tooltipArrow} />
          </View>
        )}
      </View>

      {/* X-axis labels */}
      {labels && (
        <View style={[styles.xAxisLabels, { width: chartWidth }]}>
          {labels.map((label, i) => (
            <Text key={i} style={styles.axisLabel}>{label}</Text>
          ))}
        </View>
      )}
    </View>
  );
};

// ===== INTERACTIVE BAR CHART =====
interface BarChartProps {
  data: { value: number; label: string; color?: string }[];
  height?: number;
  showValues?: boolean;
  animated?: boolean;
  onBarPress?: (index: number, value: number) => void;
}

export const InteractiveBarChart: React.FC<BarChartProps> = ({
  data,
  height = 180,
  showValues = true,
  animated = true,
  onBarPress,
}) => {
  const [selectedBar, setSelectedBar] = useState<number | null>(null);
  const animValues = useRef(data.map(() => new Animated.Value(0))).current;

  useEffect(() => {
    if (animated) {
      Animated.stagger(100, animValues.map(v =>
        Animated.timing(v, { toValue: 1, duration: 400, useNativeDriver: false })
      )).start();
    } else {
      animValues.forEach(v => v.setValue(1));
    }
  }, [data]);

  const max = Math.max(...data.map(d => d.value));
  const barWidth = (SCREEN_WIDTH - spacing.screenPadding * 2 - 40) / data.length;

  return (
    <View style={[styles.barChartContainer, { height }]}>
      {data.map((bar, i) => {
        const barHeight = (bar.value / max) * (height - 30);
        const isSelected = selectedBar === i;
        const barColor = bar.color || colors.primary;

        return (
          <TouchableOpacity
            key={i}
            style={styles.barColumn}
            onPress={() => {
              setSelectedBar(i);
              onBarPress?.(i, bar.value);
            }}
            activeOpacity={0.7}
          >
            {/* Value label */}
            {showValues && isSelected && (
              <View style={styles.barValueLabel}>
                <Text style={[styles.barValueText, { color: barColor }]}>{bar.value}</Text>
              </View>
            )}

            {/* Bar */}
            <Animated.View
              style={[
                styles.bar,
                {
                  width: barWidth * 0.6,
                  height: barHeight,
                  backgroundColor: barColor + (isSelected ? '' : 'CC'),
                  borderTopLeftRadius: 6,
                  borderTopRightRadius: 6,
                  transform: [{ scaleY: animValues[i] }],
                  shadowColor: isSelected ? barColor : 'transparent',
                  shadowOffset: { width: 0, height: 2 },
                  shadowOpacity: isSelected ? 0.4 : 0,
                  shadowRadius: isSelected ? 6 : 0,
                },
              ]}
            />

            {/* Label */}
            <Text style={[styles.barLabel, isSelected && { color: barColor, fontWeight: '700' }]}>
              {bar.label}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
};

// ===== INTERACTIVE RING CHART =====
interface RingChartProps {
  segments: { value: number; color: string; label: string }[];
  size?: number;
  strokeWidth?: number;
  centerLabel?: string;
  centerValue?: string;
  onSegmentPress?: (index: number) => void;
}

export const InteractiveRingChart: React.FC<RingChartProps> = ({
  segments,
  size = 160,
  strokeWidth = 20,
  centerLabel,
  centerValue,
  onSegmentPress,
}) => {
  const [selectedSegment, setSelectedSegment] = useState<number | null>(null);
  const animValue = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(animValue, { toValue: 1, duration: 1000, useNativeDriver: false }).start();
  }, []);

  const total = segments.reduce((sum, s) => sum + s.value, 0);
  const radius = (size - strokeWidth) / 2;

  return (
    <View style={styles.ringChartContainer}>
      <View style={[styles.ringChartOuter, { width: size, height: size, borderRadius: size / 2 }]}>
        {segments.map((segment, i) => {
          const isSelected = selectedSegment === i;
          return (
            <TouchableOpacity
              key={i}
              style={styles.ringSegment}
              onPress={() => {
                setSelectedSegment(i);
                onSegmentPress?.(i);
              }}
            >
              <View
                style={[
                  styles.ringSegmentDot,
                  {
                    width: isSelected ? 12 : 8,
                    height: isSelected ? 12 : 8,
                    borderRadius: 6,
                    backgroundColor: segment.color,
                    borderWidth: isSelected ? 2 : 0,
                    borderColor: '#FFF',
                  },
                ]}
              />
            </TouchableOpacity>
          );
        })}

        {/* Center */}
        <View style={styles.ringCenter}>
          {centerValue && <Text style={styles.ringCenterValue}>{centerValue}</Text>}
          {centerLabel && <Text style={styles.ringCenterLabel}>{centerLabel}</Text>}
        </View>
      </View>

      {/* Legend */}
      <View style={styles.ringLegend}>
        {segments.map((segment, i) => {
          const isSelected = selectedSegment === i;
          const pct = ((segment.value / total) * 100).toFixed(0);
          return (
            <TouchableOpacity
              key={i}
              style={[styles.ringLegendItem, isSelected && { backgroundColor: segment.color + '15' }]}
              onPress={() => setSelectedSegment(i)}
            >
              <View style={[styles.ringLegendDot, { backgroundColor: segment.color }]} />
              <View>
                <Text style={[styles.ringLegendLabel, isSelected && { color: segment.color }]}>{segment.label}</Text>
                <Text style={styles.ringLegendValue}>{segment.value} ({pct}%)</Text>
              </View>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
};

// ===== SPARKLINE =====
interface SparklineProps {
  data: number[];
  color?: string;
  height?: number;
  width?: number;
  animated?: boolean;
}

export const Sparkline: React.FC<SparklineProps> = ({
  data,
  color = colors.primary,
  height = 40,
  width = 100,
  animated = true,
}) => {
  const animValue = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (animated) {
      Animated.timing(animValue, { toValue: 1, duration: 600, useNativeDriver: false }).start();
    }
  }, [data]);

  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const step = width / Math.max(1, data.length - 1);

  const points = data.map((val, i) => ({
    x: i * step,
    y: height - ((val - min) / range) * (height - 8) - 4,
  }));

  return (
    <View style={[styles.sparklineContainer, { height, width }]}>
      {points.map((p, i) => (
        <View
          key={i}
          style={[
            styles.sparklineDot,
            {
              left: p.x - 2,
              top: p.y - 2,
              width: 4,
              height: 4,
              borderRadius: 2,
              backgroundColor: color + (i === points.length - 1 ? '' : '80'),
            },
          ]}
        />
      ))}
      {/* End dot */}
      {points.length > 0 && (
        <View
          style={[
            styles.sparklineEndDot,
            {
              left: points[points.length - 1].x - 4,
              top: points[points.length - 1].y - 4,
              backgroundColor: color,
            },
          ]}
        />
      )}
    </View>
  );
};

// ===== METRIC CARD WITH CHART =====
interface MetricCardWithChartProps {
  title: string;
  value: string;
  change?: string;
  changeType?: 'up' | 'down' | 'flat';
  data: number[];
  color: string;
  icon?: string;
}

export const MetricCardWithChart: React.FC<MetricCardWithChartProps> = ({
  title, value, change, changeType, data, color, icon,
}) => (
  <View style={styles.metricCardWithChart}>
    <View style={styles.metricCardHeader}>
      <View style={[styles.metricCardIcon, { backgroundColor: color + '15' }]}>
        {icon && <Ionicons name={icon as any} size={16} color={color} />}
      </View>
      <View style={styles.metricCardInfo}>
        <Text style={styles.metricCardTitle}>{title}</Text>
        <View style={styles.metricCardValueRow}>
          <Text style={[styles.metricCardValue, { color }]}>{value}</Text>
          {change && (
            <View style={[styles.metricCardChange, { backgroundColor: changeType === 'up' ? '#22C55E15' : '#EF444415' }]}>
              <Ionicons name={changeType === 'up' ? 'trending-up' : 'trending-down'} size={10} color={changeType === 'up' ? '#22C55E' : '#EF4444'} />
              <Text style={[styles.metricCardChangeText, { color: changeType === 'up' ? '#22C55E' : '#EF4444' }]}>{change}</Text>
            </View>
          )}
        </View>
      </View>
    </View>
    <Sparkline data={data} color={color} height={50} width={SCREEN_WIDTH - spacing.screenPadding * 2 - 60} />
  </View>
);

// ===== STYLES =====
const styles = StyleSheet.create({
  // Line Chart
  chartContainer: { flexDirection: 'row', paddingVertical: spacing.sm },
  yAxisLabels: { width: 35, justifyContent: 'space-between', alignItems: 'flex-end', paddingRight: spacing.xs },
  axisLabel: { fontSize: 10, color: colors.text.muted },
  chartArea: { position: 'relative', overflow: 'visible' },
  gridContainer: { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 },
  gridLine: { position: 'absolute', left: 0, right: 0, height: 1, backgroundColor: colors.surface.divider + '40' },
  dataPoint: { position: 'absolute', justifyContent: 'center', alignItems: 'center' },
  dot: { width: 8, height: 8, borderRadius: 4 },
  tooltip: {
    position: 'absolute', backgroundColor: colors.bg.elevated,
    paddingHorizontal: 10, paddingVertical: 6, borderRadius: 8,
    borderWidth: 1, borderColor: colors.surface.border,
    alignItems: 'center', zIndex: 10,
  },
  tooltipText: { fontSize: 12, fontWeight: '700', color: colors.text.primary },
  tooltipArrow: {
    position: 'absolute', bottom: -6, width: 10, height: 10,
    backgroundColor: colors.bg.elevated, transform: [{ rotate: '45deg' }],
    borderRightWidth: 1, borderBottomWidth: 1, borderColor: colors.surface.border,
  },
  xAxisLabels: { flexDirection: 'row', justifyContent: 'space-between', paddingLeft: 40, marginTop: spacing.xs },

  // Bar Chart
  barChartContainer: { flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-around', paddingHorizontal: spacing.sm },
  barColumn: { alignItems: 'center', flex: 1 },
  bar: { minHeight: 4 },
  barLabel: { fontSize: 10, color: colors.text.muted, marginTop: spacing.xs },
  barValueLabel: { backgroundColor: colors.bg.elevated, paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6, marginBottom: 4, borderWidth: 1, borderColor: colors.surface.border },
  barValueText: { fontSize: 11, fontWeight: '700' },

  // Ring Chart
  ringChartContainer: { alignItems: 'center' },
  ringChartOuter: { justifyContent: 'center', alignItems: 'center', backgroundColor: colors.bg.input, borderWidth: 1, borderColor: colors.surface.border },
  ringCenter: { alignItems: 'center' },
  ringCenterValue: { fontSize: 24, fontWeight: '800', color: colors.text.primary },
  ringCenterLabel: { fontSize: 11, color: colors.text.muted },
  ringSegment: { position: 'absolute' },
  ringSegmentDot: {},
  ringLegend: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginTop: spacing.lg, justifyContent: 'center' },
  ringLegendItem: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs, paddingHorizontal: spacing.sm, paddingVertical: spacing.xs, borderRadius: 8 },
  ringLegendDot: { width: 8, height: 8, borderRadius: 4 },
  ringLegendLabel: { fontSize: 12, fontWeight: '600', color: colors.text.secondary },
  ringLegendValue: { fontSize: 10, color: colors.text.muted },

  // Sparkline
  sparklineContainer: { position: 'relative' },
  sparklineDot: { position: 'absolute' },
  sparklineEndDot: { position: 'absolute', width: 8, height: 8, borderRadius: 4 },

  // Metric Card with Chart
  metricCardWithChart: {
    backgroundColor: colors.bg.card, borderRadius: radius.lg, padding: spacing.lg,
    borderWidth: 1, borderColor: colors.surface.border, marginBottom: spacing.md,
  },
  metricCardHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, marginBottom: spacing.md },
  metricCardIcon: { width: 36, height: 36, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  metricCardInfo: { flex: 1 },
  metricCardTitle: { fontSize: 13, fontWeight: '600', color: colors.text.muted },
  metricCardValueRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  metricCardValue: { fontSize: 22, fontWeight: '800' },
  metricCardChange: { flexDirection: 'row', alignItems: 'center', gap: 2, paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 },
  metricCardChangeText: { fontSize: 11, fontWeight: '600' },
});
