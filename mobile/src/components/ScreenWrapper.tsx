/**
 * ScreenWrapper — Universal Premium Screen Container
 * Back button, animated header, safe area, pull-to-refresh, loading/empty states
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  RefreshControl, Animated, Dimensions, Platform, ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { colors, spacing, radius } from '../theme';
import { Skeleton } from './AnimationSystem';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const HEADER_HEIGHT = 160;
const COLLAPSE_THRESHOLD = 120;

interface ScreenWrapperProps {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
  gradient?: string[];
  backable?: boolean;
  rightAction?: { icon: string; onPress: () => void };
  refreshing?: boolean;
  onRefresh?: () => Promise<void>;
  loading?: boolean;
  loadingType?: 'skeleton' | 'spinner';
  empty?: boolean;
  emptyIcon?: string;
  emptyTitle?: string;
  emptyMessage?: string;
  emptyAction?: { label: string; onPress: () => void };
  scrollRef?: React.RefObject<ScrollView>;
  contentContainerStyle?: any;
  statusBarColor?: string;
}

export const ScreenWrapper: React.FC<ScreenWrapperProps> = ({
  children, title, subtitle, gradient, backable = true, rightAction,
  refreshing = false, onRefresh, loading = false, loadingType = 'spinner',
  empty = false, emptyIcon = 'document-text', emptyTitle = 'No Data',
  emptyMessage = 'Nothing to show here yet.', emptyAction,
  scrollRef, contentContainerStyle, statusBarColor,
}) => {
  const router = useRouter();
  const scrollY = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(20)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 400, useNativeDriver: true }),
      Animated.timing(slideAnim, { toValue: 0, duration: 400, useNativeDriver: true }),
    ]).start();
  }, []);

  // Collapsible header interpolation
  const headerHeight = scrollY.interpolate({
    inputRange: [0, COLLAPSE_THRESHOLD],
    outputRange: [HEADER_HEIGHT, 70],
    extrapolate: 'clamp',
  });

  const headerOpacity = scrollY.interpolate({
    inputRange: [0, COLLAPSE_THRESHOLD / 2, COLLAPSE_THRESHOLD],
    outputRange: [1, 0.8, 0.95],
    extrapolate: 'clamp',
  });

  const titleScale = scrollY.interpolate({
    inputRange: [0, COLLAPSE_THRESHOLD],
    outputRange: [1, 0.85],
    extrapolate: 'clamp',
  });

  const subtitleOpacity = scrollY.interpolate({
    inputRange: [0, COLLAPSE_THRESHOLD / 2],
    outputRange: [1, 0],
    extrapolate: 'clamp',
  });

  const handleBack = () => {
    Haptics.selectionAsync();
    router.back();
  };

  // Loading state
  if (loading) {
    return (
      <View style={styles.container}>
        {renderHeader()}
        <View style={styles.loadingContainer}>
          {loadingType === 'spinner' ? (
            <ActivityIndicator size="large" color={colors.primary} />
          ) : (
            <View style={styles.skeletonContainer}>
              {Array.from({ length: 5 }).map((_, i) => (
                <View key={i} style={styles.skeletonCard}>
                  <Skeleton width="60%" height={16} />
                  <Skeleton width="100%" height={12} style={{ marginTop: 8 }} />
                  <Skeleton width="80%" height={12} style={{ marginTop: 6 }} />
                </View>
              ))}
            </View>
          )}
        </View>
      </View>
    );
  }

  // Empty state
  if (empty) {
    return (
      <View style={styles.container}>
        {renderHeader()}
        <View style={styles.emptyContainer}>
          <View style={styles.emptyIconContainer}>
            <Ionicons name={emptyIcon as any} size={48} color={colors.text.muted} />
          </View>
          <Text style={styles.emptyTitle}>{emptyTitle}</Text>
          <Text style={styles.emptyMessage}>{emptyMessage}</Text>
          {emptyAction && (
            <TouchableOpacity style={styles.emptyAction} onPress={emptyAction.onPress}>
              <Text style={styles.emptyActionText}>{emptyAction.label}</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>
    );
  }

  function renderHeader() {
    return (
      <Animated.View style={[styles.header, { height: headerHeight, opacity: headerOpacity }]}>
        {gradient ? (
          <LinearGradient colors={gradient as any} style={StyleSheet.absoluteFill} />
        ) : (
          <View style={[StyleSheet.absoluteFill, { backgroundColor: colors.bg.primary }]} />
        )}
        <View style={styles.headerContent}>
          <View style={styles.headerLeft}>
            {backable && (
              <TouchableOpacity style={styles.backBtn} onPress={handleBack}>
                <Ionicons name="chevron-back" size={24} color={gradient ? '#FFF' : colors.text.primary} />
              </TouchableOpacity>
            )}
            <Animated.View style={{ flex: 1, transform: [{ scale: titleScale }] }}>
              <Text style={[styles.headerTitle, gradient && { color: '#FFF' }]} numberOfLines={1}>{title}</Text>
              {subtitle && (
                <Animated.Text style={[styles.headerSubtitle, gradient && { color: 'rgba(255,255,255,0.7)' }, { opacity: subtitleOpacity }]} numberOfLines={1}>
                  {subtitle}
                </Animated.Text>
              )}
            </Animated.View>
          </View>
          {rightAction && (
            <TouchableOpacity onPress={rightAction.onPress} style={[styles.headerAction, gradient && { backgroundColor: 'rgba(255,255,255,0.15)' }]}>
              <Ionicons name={rightAction.icon as any} size={20} color={gradient ? '#FFF' : colors.primary} />
            </TouchableOpacity>
          )}
        </View>
      </Animated.View>
    );
  }

  return (
    <View style={styles.container}>
      {renderHeader()}
      <Animated.ScrollView
        ref={scrollRef}
        style={styles.scrollView}
        contentContainerStyle={[styles.scrollContent, contentContainerStyle]}
        onScroll={Animated.event([{ nativeEvent: { contentOffset: { y: scrollY } } }], { useNativeDriver: false })}
        scrollEventThrottle={16}
        refreshControl={onRefresh ? (
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />
        ) : undefined}
        showsVerticalScrollIndicator={false}
      >
        <Animated.View style={{ opacity: fadeAnim, transform: [{ translateY: slideAnim }] }}>
          {children}
        </Animated.View>
        <View style={{ height: 100 }} />
      </Animated.ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  header: { justifyContent: 'flex-end', paddingBottom: spacing.md },
  headerContent: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: spacing.screenPadding },
  headerLeft: { flexDirection: 'row', alignItems: 'center', flex: 1, gap: spacing.xs },
  backBtn: { padding: spacing.xs },
  headerTitle: { fontSize: 20, fontWeight: '800', color: colors.text.primary },
  headerSubtitle: { fontSize: 12, color: colors.text.muted, marginTop: 2 },
  headerAction: { width: 36, height: 36, borderRadius: 18, backgroundColor: colors.primaryMuted, justifyContent: 'center', alignItems: 'center' },
  scrollView: { flex: 1 },
  scrollContent: { paddingTop: spacing.sm },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  skeletonContainer: { paddingHorizontal: spacing.screenPadding, gap: spacing.md },
  skeletonCard: { backgroundColor: colors.bg.card, borderRadius: radius.lg, padding: spacing.lg, borderWidth: 1, borderColor: colors.surface.border },
  emptyContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingHorizontal: spacing.xl },
  emptyIconContainer: { width: 80, height: 80, borderRadius: 40, backgroundColor: colors.bg.card, justifyContent: 'center', alignItems: 'center', marginBottom: spacing.lg, borderWidth: 1, borderColor: colors.surface.border },
  emptyTitle: { fontSize: 18, fontWeight: '700', color: colors.text.primary, marginBottom: spacing.sm },
  emptyMessage: { fontSize: 14, color: colors.text.muted, textAlign: 'center', lineHeight: 20 },
  emptyAction: { marginTop: spacing.xl, paddingHorizontal: spacing.xl, paddingVertical: spacing.md, backgroundColor: colors.primary, borderRadius: radius.button },
  emptyActionText: { fontSize: 15, fontWeight: '700', color: '#FFF' },
});
