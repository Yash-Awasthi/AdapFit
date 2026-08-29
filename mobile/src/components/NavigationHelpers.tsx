/**
 * Navigation Helpers — Back Button, Headers, Bottom Sheet, Navigation Utilities
 * Consistent navigation patterns across the app
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, Animated,
  Dimensions, Platform, Modal, ScrollView,
} from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../theme';
import * as Haptics from 'expo-haptics';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

// ===== BACK BUTTON =====
interface BackButtonProps {
  onPress?: () => void;
  color?: string;
  size?: number;
  withLabel?: boolean;
}

export const BackButton: React.FC<BackButtonProps> = ({
  onPress, color = colors.text.primary, size = 24, withLabel = false,
}) => {
  const router = useRouter();
  return (
    <TouchableOpacity
      style={styles.backButton}
      onPress={() => {
        Haptics.selectionAsync();
        onPress ? onPress() : router.back();
      }}
      hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
    >
      <Ionicons name="chevron-back" size={size} color={color} />
      {withLabel && <Text style={[styles.backLabel, { color }]}>Back</Text>}
    </TouchableOpacity>
  );
};

// ===== SCREEN HEADER =====
interface ScreenHeaderProps {
  title: string;
  subtitle?: string;
  gradient?: string[];
  backable?: boolean;
  rightAction?: { icon: string; onPress: () => void };
  rightLabel?: string;
  large?: boolean;
}

export const ScreenHeader: React.FC<ScreenHeaderProps> = ({
  title, subtitle, gradient, backable = true, rightAction, rightLabel, large,
}) => {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(20)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 400, useNativeDriver: true }),
      Animated.timing(slideAnim, { toValue: 0, duration: 400, useNativeDriver: true }),
    ]).start();
  }, []);

  const content = (
    <View style={styles.headerContent}>
      <View style={styles.headerLeft}>
        {backable && <BackButton color={gradient ? '#FFF' : colors.text.primary} />}
        <View style={{ flex: 1 }}>
          <Text style={[large ? styles.headerTitleLarge : styles.headerTitle, gradient && { color: '#FFF' }]}>{title}</Text>
          {subtitle && <Text style={[styles.headerSubtitle, gradient && { color: 'rgba(255,255,255,0.7)' }]}>{subtitle}</Text>}
        </View>
      </View>
      {rightAction && (
        <TouchableOpacity style={[styles.headerAction, gradient && { backgroundColor: 'rgba(255,255,255,0.15)' }]} onPress={rightAction.onPress}>
          <Ionicons name={rightAction.icon as any} size={20} color={gradient ? '#FFF' : colors.primary} />
          {rightLabel && <Text style={[styles.headerActionLabel, gradient && { color: '#FFF' }]}>{rightLabel}</Text>}
        </TouchableOpacity>
      )}
    </View>
  );

  return (
    <Animated.View style={{ opacity: fadeAnim, transform: [{ translateY: slideAnim }] }}>
      {gradient ? (
        <LinearGradient colors={gradient as any} style={styles.headerGradient}>
          {content}
        </LinearGradient>
      ) : (
        <View style={styles.headerPlain}>{content}</View>
      )}
    </Animated.View>
  );
};

// ===== BOTTOM SHEET =====
interface BottomSheetProps {
  visible: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  height?: number;
}

export const BottomSheet: React.FC<BottomSheetProps> = ({
  visible, onClose, title, children, height = SCREEN_HEIGHT * 0.5,
}) => {
  const slideAnim = useRef(new Animated.Value(SCREEN_HEIGHT)).current;
  const opacityAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visible) {
      Animated.parallel([
        Animated.spring(slideAnim, { toValue: 0, useNativeDriver: true, tension: 50, friction: 10 }),
        Animated.timing(opacityAnim, { toValue: 1, duration: 200, useNativeDriver: true }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.timing(slideAnim, { toValue: SCREEN_HEIGHT, duration: 250, useNativeDriver: true }),
        Animated.timing(opacityAnim, { toValue: 0, duration: 200, useNativeDriver: true }),
      ]).start();
    }
  }, [visible]);

  if (!visible) return null;

  return (
    <Animated.View style={[styles.bottomSheetOverlay, { opacity: opacityAnim }]}>
      <TouchableOpacity style={styles.bottomSheetBackdrop} onPress={onClose} activeOpacity={1} />
      <Animated.View style={[styles.bottomSheet, { height, transform: [{ translateY: slideAnim }] }]}>
        {/* Handle */}
        <View style={styles.bottomSheetHandle}>
          <View style={styles.bottomSheetHandleBar} />
        </View>
        {title && (
          <View style={styles.bottomSheetHeader}>
            <Text style={styles.bottomSheetTitle}>{title}</Text>
            <TouchableOpacity onPress={onClose}>
              <Ionicons name="close-circle" size={24} color={colors.text.muted} />
            </TouchableOpacity>
          </View>
        )}
        <ScrollView style={styles.bottomSheetContent} showsVerticalScrollIndicator={false}>
          {children}
        </ScrollView>
      </Animated.View>
    </Animated.View>
  );
};

// ===== FLOATING ACTION BUTTON =====
interface FABProps {
  icon: string;
  onPress: () => void;
  color?: string;
  label?: string;
  position?: { bottom?: number; right?: number };
}

export const FloatingActionButton: React.FC<FABProps> = ({
  icon, onPress, color = colors.primary, label, position,
}) => {
  const scaleAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, tension: 50, friction: 5, delay: 300 }).start();
  }, []);

  return (
    <Animated.View
      style={[
        styles.fab,
        {
          backgroundColor: color,
          transform: [{ scale: scaleAnim }],
          bottom: (position?.bottom ?? 24) + 70, // Above tab bar
          right: position?.right ?? 20,
        },
      ]}
    >
      <TouchableOpacity
        style={styles.fabTouchable}
        onPress={() => {
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
          onPress();
        }}
        activeOpacity={0.8}
      >
        <Ionicons name={icon as any} size={24} color="#FFF" />
        {label && <Text style={styles.fabLabel}>{label}</Text>}
      </TouchableOpacity>
    </Animated.View>
  );
};

// ===== SECTION DIVIDER =====
export const SectionDivider: React.FC<{ label?: string }> = ({ label }) => (
  <View style={styles.sectionDivider}>
    <View style={styles.dividerLine} />
    {label && <Text style={styles.dividerLabel}>{label}</Text>}
    <View style={styles.dividerLine} />
  </View>
);

// ===== EMPTY STATE =====
interface EmptyStateProps {
  icon: string;
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ icon, title, message, actionLabel, onAction }) => (
  <View style={styles.emptyState}>
    <View style={styles.emptyStateIcon}>
      <Ionicons name={icon as any} size={48} color={colors.text.muted} />
    </View>
    <Text style={styles.emptyStateTitle}>{title}</Text>
    <Text style={styles.emptyStateMessage}>{message}</Text>
    {actionLabel && onAction && (
      <TouchableOpacity style={styles.emptyStateAction} onPress={onAction}>
        <Text style={styles.emptyStateActionText}>{actionLabel}</Text>
      </TouchableOpacity>
    )}
  </View>
);

// ===== STYLES =====
const styles = StyleSheet.create({
  // Back Button
  backButton: { flexDirection: 'row', alignItems: 'center', padding: spacing.xs },
  backLabel: { fontSize: 15, fontWeight: '500', marginLeft: 2 },

  // Screen Header
  headerGradient: { paddingTop: Platform.OS === 'ios' ? 56 : 48, paddingBottom: spacing.xl, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 28, borderBottomRightRadius: 28 },
  headerPlain: { paddingTop: Platform.OS === 'ios' ? 56 : 48, paddingBottom: spacing.lg, paddingHorizontal: spacing.screenPadding },
  headerContent: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  headerLeft: { flexDirection: 'row', alignItems: 'center', flex: 1, gap: spacing.xs },
  headerTitle: { fontSize: 22, fontWeight: '800', color: colors.text.primary },
  headerTitleLarge: { fontSize: 28, fontWeight: '800', color: colors.text.primary },
  headerSubtitle: { fontSize: 13, color: colors.text.muted, marginTop: 2 },
  headerAction: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 999, backgroundColor: colors.primaryMuted },
  headerActionLabel: { fontSize: 13, fontWeight: '600', color: colors.primary },

  // Bottom Sheet
  bottomSheetOverlay: { ...StyleSheet.absoluteFillObject, zIndex: 10000 },
  bottomSheetBackdrop: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(0,0,0,0.5)' },
  bottomSheet: { position: 'absolute', bottom: 0, left: 0, right: 0, backgroundColor: colors.bg.card, borderTopLeftRadius: 24, borderTopRightRadius: 24 },
  bottomSheetHandle: { alignItems: 'center', paddingVertical: spacing.md },
  bottomSheetHandleBar: { width: 40, height: 4, borderRadius: 2, backgroundColor: colors.surface.divider },
  bottomSheetHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: spacing.screenPadding, paddingBottom: spacing.md },
  bottomSheetTitle: { fontSize: 18, fontWeight: '700', color: colors.text.primary },
  bottomSheetContent: { flex: 1, paddingHorizontal: spacing.screenPadding },

  // FAB
  fab: { position: 'absolute', width: 56, height: 56, borderRadius: 28, justifyContent: 'center', alignItems: 'center', zIndex: 100, ...Platform.select({ ios: { shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 8 }, android: { elevation: 8 } }) },
  fabTouchable: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  fabLabel: { fontSize: 10, fontWeight: '700', color: '#FFF', marginTop: 2 },

  // Section Divider
  sectionDivider: { flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.lg, paddingHorizontal: spacing.screenPadding },
  dividerLine: { flex: 1, height: 1, backgroundColor: colors.surface.divider },
  dividerLabel: { fontSize: 12, fontWeight: '600', color: colors.text.muted, marginHorizontal: spacing.md },

  // Empty State
  emptyState: { alignItems: 'center', paddingVertical: spacing['4xl'], paddingHorizontal: spacing.screenPadding },
  emptyStateIcon: { width: 80, height: 80, borderRadius: 40, backgroundColor: colors.bg.card, justifyContent: 'center', alignItems: 'center', marginBottom: spacing.lg, borderWidth: 1, borderColor: colors.surface.border },
  emptyStateTitle: { fontSize: 18, fontWeight: '700', color: colors.text.primary, marginBottom: spacing.sm },
  emptyStateMessage: { fontSize: 14, color: colors.text.muted, textAlign: 'center', lineHeight: 20 },
  emptyStateAction: { marginTop: spacing.lg, paddingHorizontal: spacing.xl, paddingVertical: spacing.md, backgroundColor: colors.primary, borderRadius: radius.button },
  emptyStateActionText: { fontSize: 15, fontWeight: '700', color: '#FFF' },
});
