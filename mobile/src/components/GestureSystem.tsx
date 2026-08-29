/**
 * Gesture System — Swipe, Pull, Tap, Long Press Utilities
 * Enhanced UX with haptic feedback and smooth transitions
 */
import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, Animated,
  PanResponder, Dimensions, Platform, Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../theme';
import * as Haptics from 'expo-haptics';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
const SWIPE_THRESHOLD = 80;

// ===== SWIPEABLE CARD =====
interface SwipeableCardProps {
  children: React.ReactNode;
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  leftAction?: { icon: string; color: string; label: string };
  rightAction?: { icon: string; color: string; label: string };
  style?: any;
}

export const SwipeableCard: React.FC<SwipeableCardProps> = ({
  children, onSwipeLeft, onSwipeRight, leftAction, rightAction, style,
}) => {
  const translateX = useRef(new Animated.Value(0)).current;
  const [swiping, setSwiping] = useState(false);

  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: () => true,
      onPanResponderMove: (_, gesture) => {
        translateX.setValue(gesture.dx);
        setSwiping(true);
      },
      onPanResponderRelease: (_, gesture) => {
        if (gesture.dx < -SWIPE_THRESHOLD && onSwipeLeft) {
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
          onSwipeLeft();
        } else if (gesture.dx > SWIPE_THRESHOLD && onSwipeRight) {
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
          onSwipeRight();
        }
        Animated.spring(translateX, { toValue: 0, useNativeDriver: true }).start();
        setSwiping(false);
      },
    })
  ).current;

  const leftActionOpacity = translateX.interpolate({
    inputRange: [-100, -50, 0],
    outputRange: [1, 0.5, 0],
  });
  const rightActionOpacity = translateX.interpolate({
    inputRange: [0, 50, 100],
    outputRange: [0, 0.5, 1],
  });

  return (
    <View style={[styles.swipeableContainer, style]}>
      {/* Left Action */}
      {leftAction && (
        <Animated.View style={[styles.swipeActionLeft, { opacity: leftActionOpacity, backgroundColor: leftAction.color }]}>
          <Ionicons name={leftAction.icon as any} size={24} color="#FFF" />
          <Text style={styles.swipeActionText}>{leftAction.label}</Text>
        </Animated.View>
      )}

      {/* Right Action */}
      {rightAction && (
        <Animated.View style={[styles.swipeActionRight, { opacity: rightActionOpacity, backgroundColor: rightAction.color }]}>
          <Ionicons name={rightAction.icon as any} size={24} color="#FFF" />
          <Text style={styles.swipeActionText}>{rightAction.label}</Text>
        </Animated.View>
      )}

      {/* Card Content */}
      <Animated.View
        style={[styles.swipeableContent, { transform: [{ translateX }] }]}
        {...panResponder.panHandlers}
      >
        {children}
      </Animated.View>
    </View>
  );
};

// ===== PULL TO REFRESH =====
interface PullToRefreshProps {
  children: React.ReactNode;
  onRefresh: () => Promise<void>;
  color?: string;
}

export const PullToRefresh: React.FC<PullToRefreshProps> = ({ children, onRefresh, color = colors.primary }) => {
  const [refreshing, setRefreshing] = useState(false);
  const spinAnim = useRef(new Animated.Value(0)).current;

  const handleRefresh = async () => {
    setRefreshing(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    Animated.loop(Animated.timing(spinAnim, { toValue: 1, duration: 1000, useNativeDriver: true })).start();
    await onRefresh();
    spinAnim.stopAnimation();
    spinAnim.setValue(0);
    setRefreshing(false);
  };

  return (
    <View style={styles.pullContainer}>
      {refreshing && (
        <View style={styles.refreshIndicator}>
          <Animated.View style={{ transform: [{ rotate: spinAnim.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '360deg'] }) }] }}>
            <Ionicons name="refresh" size={20} color={color} />
          </Animated.View>
        </View>
      )}
      {children}
    </View>
  );
};

// ===== SWIPEABLE TAB BAR =====
interface SwipeableTabBarProps {
  tabs: { label: string; icon?: string }[];
  activeTab: number;
  onTabChange: (index: number) => void;
  color?: string;
}

export const SwipeableTabBar: React.FC<SwipeableTabBarProps> = ({
  tabs, activeTab, onTabChange, color = colors.primary,
}) => {
  const translateX = useRef(new Animated.Value(0)).current;
  const tabWidth = SCREEN_WIDTH / tabs.length;

  useEffect(() => {
    Animated.spring(translateX, { toValue: activeTab * tabWidth, useNativeDriver: true, tension: 50, friction: 10 }).start();
  }, [activeTab]);

  return (
    <View style={styles.tabBarContainer}>
      <View style={styles.tabBar}>
        {tabs.map((tab, i) => (
          <TouchableOpacity
            key={i}
            style={styles.tabItem}
            onPress={() => {
              Haptics.selectionAsync();
              onTabChange(i);
            }}
          >
            {tab.icon && (
              <Ionicons
                name={tab.icon as any}
                size={18}
                color={activeTab === i ? color : colors.text.muted}
              />
            )}
            <Text style={[styles.tabLabel, activeTab === i && { color, fontWeight: '700' }]}>{tab.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <Animated.View
        style={[
          styles.tabIndicator,
          {
            width: tabWidth,
            backgroundColor: color,
            transform: [{ translateX }],
          },
        ]}
      />
    </View>
  );
};

// ===== HAPTIC BUTTON =====
interface HapticButtonProps {
  children: React.ReactNode;
  onPress: () => void;
  haptic?: 'light' | 'medium' | 'heavy' | 'selection' | 'success' | 'warning' | 'error';
  style?: any;
  disabled?: boolean;
}

export const HapticButton: React.FC<HapticButtonProps> = ({
  children, onPress, haptic = 'medium', style, disabled,
}) => {
  const scaleAnim = useRef(new Animated.Value(1)).current;

  const handlePressIn = () => {
    Animated.spring(scaleAnim, { toValue: 0.95, useNativeDriver: true }).start();
  };

  const handlePressOut = () => {
    Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, tension: 50, friction: 3 }).start();
  };

  const handlePress = () => {
    const hapticMap: Record<string, any> = {
      light: Haptics.ImpactFeedbackStyle.Light,
      medium: Haptics.ImpactFeedbackStyle.Medium,
      heavy: Haptics.ImpactFeedbackStyle.Heavy,
      selection: Haptics.ImpactFeedbackStyle.Light,
      success: Haptics.ImpactFeedbackStyle.Heavy,
      warning: Haptics.ImpactFeedbackStyle.Medium,
      error: Haptics.ImpactFeedbackStyle.Light,
    };

    Haptics.impactAsync(hapticMap[haptic] || Haptics.ImpactFeedbackStyle.Medium);
    onPress();
  };

  return (
    <Animated.View style={[{ transform: [{ scale: scaleAnim }] }, style]}>
      <TouchableOpacity
        onPress={handlePress}
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        disabled={disabled}
        activeOpacity={0.8}
      >
        {children}
      </TouchableOpacity>
    </Animated.View>
  );
};

// ===== LONG PRESS CARD =====
interface LongPressCardProps {
  children: React.ReactNode;
  onLongPress: () => void;
  onPress?: () => void;
  style?: any;
}

export const LongPressCard: React.FC<LongPressCardProps> = ({ children, onLongPress, onPress, style }) => {
  const scaleAnim = useRef(new Animated.Value(1)).current;

  return (
    <Animated.View style={[{ transform: [{ scale: scaleAnim }] }, style]}>
      <TouchableOpacity
        onPress={onPress}
        onPressIn={() => Animated.spring(scaleAnim, { toValue: 0.97, useNativeDriver: true }).start()}
        onPressOut={() => Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, tension: 50, friction: 3 }).start()}
        onLongPress={() => {
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
          onLongPress();
        }}
        activeOpacity={0.9}
      >
        {children}
      </TouchableOpacity>
    </Animated.View>
  );
};

// ===== STYLES =====
const styles = StyleSheet.create({
  // Swipeable Card
  swipeableContainer: { overflow: 'hidden', borderRadius: radius.lg },
  swipeActionLeft: { position: 'absolute', left: 0, top: 0, bottom: 0, width: 100, justifyContent: 'center', alignItems: 'center', borderRadius: radius.lg },
  swipeActionRight: { position: 'absolute', right: 0, top: 0, bottom: 0, width: 100, justifyContent: 'center', alignItems: 'center', borderRadius: radius.lg },
  swipeActionText: { fontSize: 12, fontWeight: '700', color: '#FFF', marginTop: 4 },
  swipeableContent: { backgroundColor: colors.bg.card },

  // Pull to Refresh
  pullContainer: { flex: 1 },
  refreshIndicator: { alignItems: 'center', paddingVertical: spacing.md },

  // Tab Bar
  tabBarContainer: { position: 'relative' },
  tabBar: { flexDirection: 'row', backgroundColor: colors.bg.card },
  tabItem: { flex: 1, alignItems: 'center', paddingVertical: spacing.md, gap: 4 },
  tabLabel: { fontSize: 12, color: colors.text.muted },
  tabIndicator: { position: 'absolute', bottom: 0, height: 3, borderRadius: 1.5 },
});
