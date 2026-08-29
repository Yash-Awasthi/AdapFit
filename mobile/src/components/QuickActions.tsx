/**
 * Quick Actions System — Quick Log, SOS, Measurement, Context Suggestions
 * One-tap health logging and emergency access
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, Animated,
  Dimensions, Platform, ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { colors, spacing, radius } from '../theme';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
const API = 'http://localhost:8000/api/v1';

const api = async (path: string, opts?: RequestInit) => {
  try {
    const r = await fetch(`${API}${path}`, { headers: { 'Content-Type': 'application/json' }, ...opts });
    return r.ok ? await r.json() : null;
  } catch { return null; }
};

// ===== QUICK LOG BUTTON =====
interface QuickLogItemProps {
  icon: string;
  label: string;
  color: string;
  value?: string;
  onTap: () => void;
  delay?: number;
}

const QuickLogItem: React.FC<QuickLogItemProps> = ({ icon, label, color, value, onTap, delay = 0 }) => {
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const enterAnim = useRef(new Animated.Value(0)).current;
  const [logged, setLogged] = useState(false);

  useEffect(() => {
    Animated.timing(enterAnim, { toValue: 1, duration: 400, delay, useNativeDriver: true }).start();
  }, []);

  const handleTap = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    Animated.sequence([
      Animated.spring(scaleAnim, { toValue: 0.85, useNativeDriver: true }),
      Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, tension: 50, friction: 3 }),
    ]).start();
    setLogged(true);
    onTap();
    setTimeout(() => setLogged(false), 2000);
  };

  return (
    <Animated.View style={{ opacity: enterAnim, transform: [{ scale: scaleAnim }, { translateY: enterAnim.interpolate({ inputRange: [0, 1], outputRange: [20, 0] }) }] }}>
      <TouchableOpacity style={styles.quickLogItem} onPress={handleTap} activeOpacity={0.8}>
        <View style={[styles.quickLogIcon, { backgroundColor: color + '15' }]}>
          <Ionicons name={icon as any} size={22} color={color} />
        </View>
        <Text style={styles.quickLogLabel}>{label}</Text>
        {value && <Text style={[styles.quickLogValue, { color }]}>{value}</Text>}
        {logged && (
          <View style={styles.quickLogCheck}>
            <Ionicons name="checkmark-circle" size={16} color={colors.health.calm} />
          </View>
        )}
      </TouchableOpacity>
    </Animated.View>
  );
};

// ===== QUICK LOG GRID =====
interface QuickLogGridProps {
  onLog?: (type: string) => void;
}

export const QuickLogGrid: React.FC<QuickLogGridProps> = ({ onLog }) => {
  const [waterCount, setWaterCount] = useState(0);

  const items = [
    { icon: 'water', label: 'Water', color: '#3B82F6', value: `${waterCount}/8`, onTap: () => setWaterCount(prev => prev + 1) },
    { icon: 'happy', label: 'Mood', color: '#8B5CF6', onTap: () => onLog?.('mood') },
    { icon: 'scale', label: 'Weight', color: '#22C55E', onTap: () => onLog?.('weight') },
    { icon: 'meditate', label: 'Meditate', color: '#06B6D4', onTap: () => onLog?.('meditation') },
    { icon: 'bed', label: 'Sleep', color: '#6366F1', onTap: () => onLog?.('sleep') },
    { icon: 'restaurant', label: 'Meal', color: '#F59E0B', onTap: () => onLog?.('meal') },
  ];

  return (
    <View style={styles.quickLogGrid}>
      {items.map((item, i) => (
        <QuickLogItem key={i} {...item} delay={i * 80} />
      ))}
    </View>
  );
};

// ===== EMERGENCY SOS BUTTON =====
interface EmergencySOSProps {
  onPress: () => void;
}

export const EmergencySOSButton: React.FC<EmergencySOSProps> = ({ onPress }) => {
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const glowAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.parallel([
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 1.05, duration: 1000, useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 1, duration: 1000, useNativeDriver: true }),
        ]),
        Animated.sequence([
          Animated.timing(glowAnim, { toValue: 1, duration: 1000, useNativeDriver: true }),
          Animated.timing(glowAnim, { toValue: 0, duration: 1000, useNativeDriver: true }),
        ]),
      ])
    ).start();
  }, []);

  return (
    <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
      <TouchableOpacity
        style={styles.sosButton}
        onPress={() => {
          Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
          onPress();
        }}
        activeOpacity={0.8}
      >
        <Animated.View style={[styles.sosGlow, { opacity: glowAnim }]} />
        <Ionicons name="call" size={28} color="#FFF" />
        <Text style={styles.sosLabel}>SOS</Text>
      </TouchableOpacity>
    </Animated.View>
  );
};

// ===== QUICK MEASUREMENT BUTTON =====
interface QuickMeasurementProps {
  type: 'bpm' | 'stress' | 'fatigue' | 'spo2';
  onPress: () => void;
  active?: boolean;
}

export const QuickMeasurementButton: React.FC<QuickMeasurementProps> = ({ type, onPress, active }) => {
  const config = {
    bpm: { icon: 'heart', color: colors.health.heart, label: 'Heart Rate' },
    stress: { icon: 'leaf', color: colors.health.calm, label: 'Stress' },
    fatigue: { icon: 'eye', color: colors.health.mental, label: 'Fatigue' },
    spo2: { icon: 'water', color: '#3B82F6', label: 'SpO2' },
  }[type];

  return (
    <TouchableOpacity style={[styles.measurementBtn, active && { backgroundColor: config.color + '20', borderColor: config.color + '50' }]} onPress={onPress}>
      <Ionicons name={config.icon as any} size={20} color={config.color} />
      <Text style={[styles.measurementLabel, active && { color: config.color }]}>{config.label}</Text>
      {active && <View style={[styles.measurementActiveDot, { backgroundColor: config.color }]} />}
    </TouchableOpacity>
  );
};

// ===== CONTEXT SUGGESTION =====
interface ContextSuggestionProps {
  title: string;
  description: string;
  icon: string;
  color: string;
  actionLabel: string;
  onAction: () => void;
  delay?: number;
}

export const ContextSuggestion: React.FC<ContextSuggestionProps> = ({
  title, description, icon, color, actionLabel, onAction, delay = 0,
}) => {
  const enterAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(enterAnim, { toValue: 1, duration: 400, delay, useNativeDriver: true }).start();
  }, []);

  return (
    <Animated.View style={[styles.suggestionCard, { opacity: enterAnim, transform: [{ translateX: enterAnim.interpolate({ inputRange: [0, 1], outputRange: [40, 0] }) }] }]}>
      <View style={[styles.suggestionIcon, { backgroundColor: color + '15' }]}>
        <Ionicons name={icon as any} size={20} color={color} />
      </View>
      <View style={styles.suggestionContent}>
        <Text style={styles.suggestionTitle}>{title}</Text>
        <Text style={styles.suggestionDescription}>{description}</Text>
      </View>
      <TouchableOpacity
        style={[styles.suggestionAction, { backgroundColor: color + '15' }]}
        onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); onAction(); }}
      >
        <Text style={[styles.suggestionActionText, { color }]}>{actionLabel}</Text>
      </TouchableOpacity>
    </Animated.View>
  );
};

// ===== SMART NOTIFICATION BANNER =====
interface SmartBannerProps {
  title: string;
  message: string;
  type?: 'info' | 'success' | 'warning' | 'reminder';
  actionLabel?: string;
  onAction?: () => void;
  onDismiss: () => void;
  visible: boolean;
}

export const SmartBanner: React.FC<SmartBannerProps> = ({
  title, message, type = 'info', actionLabel, onAction, onDismiss, visible,
}) => {
  const slideAnim = useRef(new Animated.Value(-100)).current;
  const opacityAnim = useRef(new Animated.Value(0)).current;

  const config = {
    info: { icon: 'information-circle', color: '#3B82F6', bg: '#3B82F612', border: '#3B82F630' },
    success: { icon: 'checkmark-circle', color: '#22C55E', bg: '#22C55E12', border: '#22C55E30' },
    warning: { icon: 'warning', color: '#F59E0B', bg: '#F59E0B12', border: '#F59E0B30' },
    reminder: { icon: 'alarm', color: '#8B5CF6', bg: '#8B5CF612', border: '#8B5CF630' },
  }[type];

  useEffect(() => {
    if (visible) {
      Animated.parallel([
        Animated.spring(slideAnim, { toValue: 0, useNativeDriver: true, tension: 50, friction: 10 }),
        Animated.timing(opacityAnim, { toValue: 1, duration: 200, useNativeDriver: true }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.timing(slideAnim, { toValue: -100, duration: 250, useNativeDriver: true }),
        Animated.timing(opacityAnim, { toValue: 0, duration: 200, useNativeDriver: true }),
      ]).start();
    }
  }, [visible]);

  if (!visible) return null;

  return (
    <Animated.View style={[styles.bannerContainer, { transform: [{ translateY: slideAnim }], opacity: opacityAnim, backgroundColor: config.bg, borderColor: config.border }]}>
      <View style={[styles.bannerIcon, { backgroundColor: config.color + '20' }]}>
        <Ionicons name={config.icon as any} size={18} color={config.color} />
      </View>
      <View style={styles.bannerContent}>
        <Text style={styles.bannerTitle}>{title}</Text>
        <Text style={styles.bannerMessage}>{message}</Text>
      </View>
      {actionLabel && onAction && (
        <TouchableOpacity onPress={onAction} style={styles.bannerAction}>
          <Text style={[styles.bannerActionText, { color: config.color }]}>{actionLabel}</Text>
        </TouchableOpacity>
      )}
      <TouchableOpacity onPress={onDismiss} style={styles.bannerDismiss}>
        <Ionicons name="close" size={16} color={colors.text.muted} />
      </TouchableOpacity>
    </Animated.View>
  );
};

// ===== SWIPEABLE QUICK SETTINGS =====
interface QuickSettingsProps {
  visible: boolean;
  onClose: () => void;
}

export const SwipeableQuickSettings: React.FC<QuickSettingsProps> = ({ visible, onClose }) => {
  const slideAnim = useRef(new Animated.Value(SCREEN_HEIGHT)).current;

  useEffect(() => {
    if (visible) {
      Animated.spring(slideAnim, { toValue: 0, useNativeDriver: true, tension: 50, friction: 10 }).start();
    } else {
      Animated.timing(slideAnim, { toValue: SCREEN_HEIGHT, duration: 250, useNativeDriver: true }).start();
    }
  }, [visible]);

  if (!visible) return null;

  return (
    <Animated.View style={[styles.settingsOverlay, { transform: [{ translateY: slideAnim }] }]}>
      <View style={styles.settingsHandle}>
        <View style={styles.settingsHandleBar} />
      </View>
      <Text style={styles.settingsTitle}>Quick Settings</Text>
      <View style={styles.settingsGrid}>
        {[
          { icon: 'moon', label: 'Dark Mode', color: '#6366F1' },
          { icon: 'notifications', label: 'Alerts', color: '#F59E0B' },
          { icon: 'location', label: 'GPS', color: '#22C55E' },
          { icon: 'bluetooth', label: 'Devices', color: '#3B82F6' },
          { icon: 'wifi', label: 'Sync', color: '#06B6D4' },
          { icon: 'lock', label: 'Privacy', color: '#EF4444' },
        ].map((item, i) => (
          <TouchableOpacity key={i} style={styles.settingsItem}>
            <View style={[styles.settingsIcon, { backgroundColor: item.color + '15' }]}>
              <Ionicons name={item.icon as any} size={20} color={item.color} />
            </View>
            <Text style={styles.settingsLabel}>{item.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  // Quick Log
  quickLogGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md, paddingHorizontal: spacing.screenPadding },
  quickLogItem: { alignItems: 'center', width: (SCREEN_WIDTH - spacing.screenPadding * 2 - spacing.md * 2) / 3 },
  quickLogIcon: { width: 56, height: 56, borderRadius: 16, justifyContent: 'center', alignItems: 'center', marginBottom: spacing.xs },
  quickLogLabel: { fontSize: 12, fontWeight: '600', color: colors.text.secondary },
  quickLogValue: { fontSize: 11, fontWeight: '700', marginTop: 2 },
  quickLogCheck: { position: 'absolute', top: -4, right: 8 },

  // SOS
  sosButton: { width: 64, height: 64, borderRadius: 32, backgroundColor: colors.health.heart, justifyContent: 'center', alignItems: 'center' },
  sosGlow: { ...StyleSheet.absoluteFillObject, borderRadius: 32, backgroundColor: colors.health.heart, opacity: 0.3 },
  sosLabel: { fontSize: 12, fontWeight: '800', color: '#FFF', marginTop: 2 },

  // Measurement
  measurementBtn: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, paddingHorizontal: spacing.lg, paddingVertical: spacing.md, borderRadius: radius.lg, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border },
  measurementLabel: { fontSize: 14, fontWeight: '600', color: colors.text.secondary },
  measurementActiveDot: { width: 8, height: 8, borderRadius: 4, marginLeft: 'auto' },

  // Suggestion
  suggestionCard: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, marginHorizontal: spacing.screenPadding, marginBottom: spacing.md, backgroundColor: colors.bg.card, padding: spacing.lg, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.surface.border },
  suggestionIcon: { width: 40, height: 40, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  suggestionContent: { flex: 1 },
  suggestionTitle: { fontSize: 14, fontWeight: '700', color: colors.text.primary },
  suggestionDescription: { fontSize: 12, color: colors.text.muted, marginTop: 2 },
  suggestionAction: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8 },
  suggestionActionText: { fontSize: 12, fontWeight: '700' },

  // Banner
  bannerContainer: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, marginHorizontal: spacing.screenPadding, marginTop: spacing.md, padding: spacing.md, borderRadius: radius.lg, borderWidth: 1 },
  bannerIcon: { width: 32, height: 32, borderRadius: 8, justifyContent: 'center', alignItems: 'center' },
  bannerContent: { flex: 1 },
  bannerTitle: { fontSize: 13, fontWeight: '700', color: colors.text.primary },
  bannerMessage: { fontSize: 11, color: colors.text.muted, marginTop: 1 },
  bannerAction: { paddingHorizontal: 8, paddingVertical: 4 },
  bannerActionText: { fontSize: 12, fontWeight: '700' },
  bannerDismiss: { padding: 4 },

  // Settings
  settingsOverlay: { position: 'absolute', bottom: 0, left: 0, right: 0, backgroundColor: colors.bg.card, borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: spacing.xl, paddingBottom: Platform.OS === 'ios' ? 40 : spacing.xl },
  settingsHandle: { alignItems: 'center', paddingVertical: spacing.md },
  settingsHandleBar: { width: 40, height: 4, borderRadius: 2, backgroundColor: colors.surface.divider },
  settingsTitle: { fontSize: 18, fontWeight: '700', color: colors.text.primary, marginBottom: spacing.lg, textAlign: 'center' },
  settingsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md },
  settingsItem: { width: '30%', alignItems: 'center', gap: spacing.xs },
  settingsIcon: { width: 48, height: 48, borderRadius: 14, justifyContent: 'center', alignItems: 'center' },
  settingsLabel: { fontSize: 11, fontWeight: '600', color: colors.text.muted },
});
