/**
 * Gesture System — Swipe, Pull, Tap, Long Press Utilities
 * Enhanced UX with haptic feedback and smooth transitions.
 * All animations use Reanimated worklets (UI thread).
 */
import React, { useState, useCallback } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, useWindowDimensions } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  runOnJS,
  FadeInDown,
} from 'react-native-reanimated';
import { GestureDetector, Gesture } from 'react-native-gesture-handler';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../theme';
import * as Haptics from 'expo-haptics';

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
  const translateX = useSharedValue(0);

  const triggerHaptic = useCallback(() => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
  }, []);

  const panGesture = Gesture.Pan()
    .onUpdate((e) => {
      translateX.value = e.translationX;
    })
    .onEnd((e) => {
      if (e.translationX < -SWIPE_THRESHOLD && onSwipeLeft) {
        runOnJS(triggerHaptic)();
        runOnJS(onSwipeLeft)();
      } else if (e.translationX > SWIPE_THRESHOLD && onSwipeRight) {
        runOnJS(triggerHaptic)();
        runOnJS(onSwipeRight)();
      }
      translateX.value = withSpring(0, { damping: 15, stiffness: 300 });
    });

  const leftActionStyle = useAnimatedStyle(() => ({
    opacity: translateX.value < -50 ? Math.min(1, Math.abs(translateX.value + 50) / 50) : 0,
  }));

  const rightActionStyle = useAnimatedStyle(() => ({
    opacity: translateX.value > 50 ? Math.min(1, (translateX.value - 50) / 50) : 0,
  }));

  const contentStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: translateX.value }],
  }));

  return (
    <View style={[styles.swipeableContainer, style]}>
      {leftAction && (
        <Animated.View style={[styles.swipeActionLeft, leftActionStyle, { backgroundColor: leftAction.color }]}>
          <Ionicons name={leftAction.icon as any} size={24} color="#FFF" />
          <Text style={styles.swipeActionText}>{leftAction.label}</Text>
        </Animated.View>
      )}

      {rightAction && (
        <Animated.View style={[styles.swipeActionRight, rightActionStyle, { backgroundColor: rightAction.color }]}>
          <Ionicons name={rightAction.icon as any} size={24} color="#FFF" />
          <Text style={styles.swipeActionText}>{rightAction.label}</Text>
        </Animated.View>
      )}

      <GestureDetector gesture={panGesture}>
        <Animated.View style={[styles.swipeableContent, contentStyle]}>
          {children}
        </Animated.View>
      </GestureDetector>
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
  const rotation = useSharedValue(0);

  const handleRefresh = async () => {
    setRefreshing(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    rotation.value = withTiming(360, { duration: 1000 });
    await onRefresh();
    rotation.value = 0;
    setRefreshing(false);
  };

  const spinStyle = useAnimatedStyle(() => ({
    transform: [{ rotate: `${rotation.value}deg` }],
  }));

  return (
    <View style={styles.pullContainer}>
      {refreshing && (
        <View style={styles.refreshIndicator}>
          <Animated.View style={spinStyle}>
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
  const { width: screenWidth } = useWindowDimensions();
  const tabWidth = screenWidth / tabs.length;
  const indicatorX = useSharedValue(0);

  React.useEffect(() => {
    indicatorX.value = withSpring(activeTab * tabWidth, { damping: 15, stiffness: 300 });
  }, [activeTab, tabWidth]);

  const indicatorStyle = useAnimatedStyle(() => ({
    width: tabWidth,
    transform: [{ translateX: indicatorX.value }],
  }));

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
        style={[styles.tabIndicator, { backgroundColor: color }, indicatorStyle]}
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
  const scale = useSharedValue(1);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const triggerHaptic = useCallback(() => {
    const hapticMap: Record<string, Haptics.ImpactFeedbackStyle> = {
      light: Haptics.ImpactFeedbackStyle.Light,
      medium: Haptics.ImpactFeedbackStyle.Medium,
      heavy: Haptics.ImpactFeedbackStyle.Heavy,
      selection: Haptics.ImpactFeedbackStyle.Light,
      success: Haptics.ImpactFeedbackStyle.Heavy,
      warning: Haptics.ImpactFeedbackStyle.Medium,
      error: Haptics.ImpactFeedbackStyle.Light,
    };
    Haptics.impactAsync(hapticMap[haptic] || Haptics.ImpactFeedbackStyle.Medium);
  }, [haptic]);

  const tapGesture = Gesture.Tap()
    .onBegin(() => {
      scale.value = withSpring(0.95, { damping: 15, stiffness: 300 });
    })
    .onFinalize(() => {
      scale.value = withSpring(1, { damping: 15, stiffness: 300 });
    })
    .onEnd(() => {
      runOnJS(triggerHaptic)();
      runOnJS(onPress)();
    });

  return (
    <GestureDetector gesture={tapGesture}>
      <Animated.View style={[animatedStyle, style]}>
        {children}
      </Animated.View>
    </GestureDetector>
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
  const scale = useSharedValue(1);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const triggerHaptic = useCallback(() => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
  }, []);

  const longPressGesture = Gesture.LongPress()
    .minDuration(500)
    .onBegin(() => {
      scale.value = withSpring(0.97, { damping: 15, stiffness: 300 });
    })
    .onFinalize(() => {
      scale.value = withSpring(1, { damping: 15, stiffness: 300 });
    })
    .onEnd(() => {
      runOnJS(triggerHaptic)();
      runOnJS(onLongPress)();
    });

  const tapGesture = Gesture.Tap()
    .onBegin(() => {
      scale.value = withSpring(0.97, { damping: 15, stiffness: 300 });
    })
    .onFinalize(() => {
      scale.value = withSpring(1, { damping: 15, stiffness: 300 });
    })
    .onEnd(() => {
      if (onPress) runOnJS(onPress)();
    });

  const composed = Gesture.Race(longPressGesture, tapGesture);

  return (
    <GestureDetector gesture={composed}>
      <Animated.View style={[animatedStyle, style]}>
        {children}
      </Animated.View>
    </GestureDetector>
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
