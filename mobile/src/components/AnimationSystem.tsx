/**
 * Animation System — Comprehensive Animation Library
 * Page transitions, card entrances, loading, success/error, scroll-triggered
 */
import React, { useEffect, useRef, useState } from 'react';
import {
  View, Text, Animated, Easing, Dimensions, StyleSheet,
  Platform, InteractionManager,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../theme';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

// ===== PAGE TRANSITION WRAPPER =====
interface PageTransitionProps {
  children: React.ReactNode;
  type?: 'slide' | 'fade' | 'zoom' | 'flip' | 'slideFromBottom';
  duration?: number;
  delay?: number;
}

export const PageTransition: React.FC<PageTransitionProps> = ({
  children, type = 'slide', duration = 400, delay = 0,
}) => {
  const animValue = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(animValue, { toValue: 1, duration, delay, useNativeDriver: true, easing: Easing.out(Easing.cubic) }).start();
  }, []);

  const getStyle = () => {
    switch (type) {
      case 'slide':
        return { transform: [{ translateX: animValue.interpolate({ inputRange: [0, 1], outputRange: [SCREEN_WIDTH, 0] }) }] };
      case 'slideFromBottom':
        return { transform: [{ translateY: animValue.interpolate({ inputRange: [0, 1], outputRange: [SCREEN_HEIGHT, 0] }) }] };
      case 'zoom':
        return { transform: [{ scale: animValue.interpolate({ inputRange: [0, 1], outputRange: [0.8, 1] }) }], opacity: animValue };
      case 'flip':
        return { transform: [{ rotateY: animValue.interpolate({ inputRange: [0, 1], outputRange: ['90deg', '0deg'] }) }], opacity: animValue };
      case 'fade':
      default:
        return { opacity: animValue };
    }
  };

  return <Animated.View style={getStyle()}>{children}</Animated.View>;
};

// ===== STAGGERED LIST =====
interface StaggeredListProps {
  children: React.ReactNode[];
  staggerDelay?: number;
  animationType?: 'slideIn' | 'fadeIn' | 'scaleIn' | 'slideDown';
  initialOffset?: number;
}

export const StaggeredList: React.FC<StaggeredListProps> = ({
  children, staggerDelay = 80, animationType = 'slideIn', initialOffset = 30,
}) => {
  return (
    <View>
      {React.Children.map(children, (child, index) => (
        <StaggeredItem
          key={index}
          delay={index * staggerDelay}
          type={animationType}
          offset={initialOffset}
        >
          {child}
        </StaggeredItem>
      ))}
    </View>
  );
};

const StaggeredItem: React.FC<{
  children: React.ReactNode;
  delay: number;
  type: string;
  offset: number;
}> = ({ children, delay, type, offset }) => {
  const animValue = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(animValue, { toValue: 1, duration: 400, delay, useNativeDriver: true, easing: Easing.out(Easing.cubic) }).start();
  }, []);

  const getStyle = () => {
    switch (type) {
      case 'slideIn':
        return {
          opacity: animValue,
          transform: [{ translateY: animValue.interpolate({ inputRange: [0, 1], outputRange: [offset, 0] }) }],
        };
      case 'fadeIn':
        return { opacity: animValue };
      case 'scaleIn':
        return {
          opacity: animValue,
          transform: [{ scale: animValue.interpolate({ inputRange: [0, 1], outputRange: [0.85, 1] }) }],
        };
      case 'slideDown':
        return {
          opacity: animValue,
          transform: [{ translateY: animValue.interpolate({ inputRange: [0, 1], outputRange: [-offset, 0] }) }],
        };
      default:
        return { opacity: animValue };
    }
  };

  return <Animated.View style={getStyle()}>{children}</Animated.View>;
};

// ===== ANIMATED CARD =====
interface AnimatedCardProps {
  children: React.ReactNode;
  onPress?: () => void;
  delay?: number;
  style?: any;
}

export const AnimatedCard: React.FC<AnimatedCardProps> = ({ children, onPress, delay = 0, style }) => {
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const enterAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(enterAnim, { toValue: 1, duration: 500, delay, useNativeDriver: true, easing: Easing.out(Easing.cubic) }).start();
  }, []);

  return (
    <Animated.View
      style={[{
        opacity: enterAnim,
        transform: [
          { translateY: enterAnim.interpolate({ inputRange: [0, 1], outputRange: [20, 0] }) },
          { scale: scaleAnim },
        ],
      }, style]}
    >
      <AnimatedTouchable
        onPressIn={() => Animated.spring(scaleAnim, { toValue: 0.97, useNativeDriver: true }).start()}
        onPressOut={() => Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, tension: 50, friction: 3 }).start()}
        onPress={onPress}
        disabled={!onPress}
      >
        {children}
      </AnimatedTouchable>
    </Animated.View>
  );
};

// Simple touchable wrapper
const AnimatedTouchable: React.FC<any> = ({ children, ...props }) => {
  const { TouchableOpacity } = require('react-native');
  return <TouchableOpacity activeOpacity={0.9} {...props}>{children}</TouchableOpacity>;
};

// ===== SKELETON LOADER =====
interface SkeletonProps {
  width?: number | string;
  height?: number;
  borderRadius?: number;
  style?: any;
}

export const Skeleton: React.FC<SkeletonProps> = ({ width = '100%', height = 20, borderRadius = 8, style }) => {
  const pulseAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1, duration: 800, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 0, duration: 800, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  return (
    <Animated.View
      style={[{
        width, height, borderRadius,
        backgroundColor: colors.surface.divider,
        opacity: pulseAnim.interpolate({ inputRange: [0, 1], outputRange: [0.3, 0.7] }),
      }, style]}
    />
  );
};

// ===== SKELETON CARD =====
export const SkeletonCard: React.FC = () => (
  <View style={styles.skeletonCard}>
    <Skeleton width="60%" height={16} />
    <Skeleton width="100%" height={12} style={{ marginTop: 8 }} />
    <Skeleton width="80%" height={12} style={{ marginTop: 6 }} />
    <View style={{ flexDirection: 'row', gap: 8, marginTop: 12 }}>
      <Skeleton width={60} height={24} borderRadius={12} />
      <Skeleton width={60} height={24} borderRadius={12} />
    </View>
  </View>
);

// ===== SUCCESS ANIMATION =====
interface SuccessAnimationProps {
  visible: boolean;
  message?: string;
  onComplete?: () => void;
  size?: number;
}

export const SuccessAnimation: React.FC<SuccessAnimationProps> = ({
  visible, message = 'Done!', onComplete, size = 80,
}) => {
  const scaleAnim = useRef(new Animated.Value(0)).current;
  const checkAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visible) {
      Animated.sequence([
        Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, tension: 80, friction: 5 }),
        Animated.timing(checkAnim, { toValue: 1, duration: 300, useNativeDriver: true }),
      ]).start(() => {
        setTimeout(() => {
          Animated.parallel([
            Animated.timing(scaleAnim, { toValue: 0, duration: 200, useNativeDriver: true }),
            Animated.timing(checkAnim, { toValue: 0, duration: 200, useNativeDriver: true }),
          ]).start(() => onComplete?.());
        }, 1500);
      });
    }
  }, [visible]);

  if (!visible) return null;

  return (
    <Animated.View style={[styles.successContainer, { transform: [{ scale: scaleAnim }] }]}>
      <View style={[styles.successCircle, { width: size, height: size, borderRadius: size / 2 }]}>
        <Animated.View style={{ transform: [{ scale: checkAnim }] }}>
          <Ionicons name="checkmark" size={size * 0.5} color="#FFF" />
        </Animated.View>
      </View>
      <Text style={styles.successMessage}>{message}</Text>
    </Animated.View>
  );
};

// ===== ERROR ANIMATION =====
interface ErrorAnimationProps {
  visible: boolean;
  message?: string;
  onComplete?: () => void;
}

export const ErrorAnimation: React.FC<ErrorAnimationProps> = ({
  visible, message = 'Something went wrong', onComplete,
}) => {
  const shakeAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visible) {
      Animated.sequence([
        Animated.timing(fadeAnim, { toValue: 1, duration: 200, useNativeDriver: true }),
        Animated.sequence([
          Animated.timing(shakeAnim, { toValue: 10, duration: 50, useNativeDriver: true }),
          Animated.timing(shakeAnim, { toValue: -10, duration: 50, useNativeDriver: true }),
          Animated.timing(shakeAnim, { toValue: 8, duration: 50, useNativeDriver: true }),
          Animated.timing(shakeAnim, { toValue: -8, duration: 50, useNativeDriver: true }),
          Animated.timing(shakeAnim, { toValue: 0, duration: 50, useNativeDriver: true }),
        ]),
      ]).start(() => {
        setTimeout(() => {
          Animated.timing(fadeAnim, { toValue: 0, duration: 300, useNativeDriver: true }).start(() => onComplete?.());
        }, 2000);
      });
    }
  }, [visible]);

  if (!visible) return null;

  return (
    <Animated.View style={[styles.errorContainer, { opacity: fadeAnim, transform: [{ translateX: shakeAnim }] }]}>
      <View style={styles.errorCircle}>
        <Ionicons name="close" size={32} color="#FFF" />
      </View>
      <Text style={styles.errorMessage}>{message}</Text>
    </Animated.View>
  );
};

// ===== PULSE ANIMATION =====
interface PulseProps {
  color?: string;
  size?: number;
  children?: React.ReactNode;
}

export const Pulse: React.FC<PulseProps> = ({ color = colors.primary, size = 100, children }) => {
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const opacityAnim = useRef(new Animated.Value(0.4)).current;

  useEffect(() => {
    Animated.loop(
      Animated.parallel([
        Animated.timing(pulseAnim, { toValue: 1.5, duration: 1000, useNativeDriver: true }),
        Animated.timing(opacityAnim, { toValue: 0, duration: 1000, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  return (
    <View style={{ width: size, height: size, justifyContent: 'center', alignItems: 'center' }}>
      <Animated.View
        style={[
          styles.pulseRing,
          {
            width: size, height: size, borderRadius: size / 2,
            backgroundColor: color,
            transform: [{ scale: pulseAnim }],
            opacity: opacityAnim,
          },
        ]}
      />
      {children && <View style={styles.pulseContent}>{children}</View>}
    </View>
  );
};

// ===== LOADING WAVE =====
interface LoadingWaveProps {
  color?: string;
  barCount?: number;
}

export const LoadingWave: React.FC<LoadingWaveProps> = ({ color = colors.primary, barCount = 5 }) => {
  const animations = useRef(Array.from({ length: barCount }, () => new Animated.Value(0.3))).current;

  useEffect(() => {
    Animated.loop(
      Animated.stagger(150, animations.map((anim, i) =>
        Animated.sequence([
          Animated.timing(anim, { toValue: 1, duration: 400, useNativeDriver: true }),
          Animated.timing(anim, { toValue: 0.3, duration: 400, useNativeDriver: true }),
        ])
      ))
    ).start();
  }, []);

  return (
    <View style={styles.waveContainer}>
      {animations.map((anim, i) => (
        <Animated.View
          key={i}
          style={[styles.waveBar, { backgroundColor: color, height: 30, opacity: anim, transform: [{ scaleY: anim }] }]}
        />
      ))}
    </View>
  );
};

// ===== CONFETTI =====
interface ConfettiProps {
  visible: boolean;
  colors?: string[];
}

export const Confetti: React.FC<ConfettiProps> = ({ visible, colors: confettiColors = ['#EF4444', '#F59E0B', '#22C55E', '#3B82F6', '#8B5CF6', '#EC4899'] }) => {
  const pieces = useRef(
    Array.from({ length: 30 }, (_, i) => ({
      x: new Animated.Value(0),
      y: new Animated.Value(-20),
      rotation: new Animated.Value(0),
      color: confettiColors[i % confettiColors.length],
      startX: Math.random() * SCREEN_WIDTH,
      delay: Math.random() * 500,
    }))
  ).current;

  useEffect(() => {
    if (visible) {
      pieces.forEach(piece => {
        Animated.parallel([
          Animated.timing(piece.y, { toValue: SCREEN_HEIGHT + 50, duration: 2000 + Math.random() * 1000, delay: piece.delay, useNativeDriver: true }),
          Animated.timing(piece.x, { toValue: (Math.random() - 0.5) * 200, duration: 2000 + Math.random() * 1000, delay: piece.delay, useNativeDriver: true }),
          Animated.timing(piece.rotation, { toValue: Math.random() * 720 - 360, duration: 2000 + Math.random() * 1000, delay: piece.delay, useNativeDriver: true }),
        ]).start();
      });
    }
  }, [visible]);

  if (!visible) return null;

  return (
    <View style={styles.confettiContainer} pointerEvents="none">
      {pieces.map((piece, i) => (
        <Animated.View
          key={i}
          style={[
            styles.confettiPiece,
            {
              left: piece.startX,
              backgroundColor: piece.color,
              transform: [
                { translateX: piece.x },
                { translateY: piece.y },
                { rotate: piece.rotation.interpolate({ inputRange: [0, 360], outputRange: ['0deg', '360deg'] }) },
              ],
            },
          ]}
        />
      ))}
    </View>
  );
};

// ===== FLOATING LABEL INPUT =====
interface FloatingLabelProps {
  label: string;
  value: string;
  onChangeText: (text: string) => void;
  secureTextEntry?: boolean;
  keyboardType?: any;
  icon?: string;
}

export const FloatingLabelInput: React.FC<FloatingLabelProps> = ({
  label, value, onChangeText, secureTextEntry, keyboardType, icon,
}) => {
  const [focused, setFocused] = useState(false);
  const labelAnim = useRef(new Animated.Value(value ? 1 : 0)).current;

  useEffect(() => {
    Animated.timing(labelAnim, {
      toValue: focused || value ? 1 : 0,
      duration: 200,
      useNativeDriver: true,
    }).start();
  }, [focused, value]);

  const labelStyle = {
    transform: [{ translateY: labelAnim.interpolate({ inputRange: [0, 1], outputRange: [18, -8] }) }],
    fontSize: labelAnim.interpolate({ inputRange: [0, 1], outputRange: [16, 12] }),
    color: labelAnim.interpolate({ inputRange: [0, 1], outputRange: [colors.text.muted, focused ? colors.primary : colors.text.muted] }),
  };

  return (
    <View style={styles.floatingInputContainer}>
      {icon && <Ionicons name={icon as any} size={18} color={focused ? colors.primary : colors.text.muted} style={styles.floatingInputIcon} />}
      <View style={[styles.floatingInputWrapper, focused && styles.floatingInputFocused]}>
        <Animated.Text style={[styles.floatingInputLabel, labelStyle]}>{label}</Animated.Text>
        <Animated.View
          style={[styles.floatingInput, { paddingLeft: icon ? 28 : 0 }]}
        />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  // Skeleton
  skeletonCard: { backgroundColor: colors.bg.card, borderRadius: radius.lg, padding: spacing.lg, borderWidth: 1, borderColor: colors.surface.border },

  // Success
  successContainer: { alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  successCircle: { backgroundColor: colors.health.calm, justifyContent: 'center', alignItems: 'center', marginBottom: spacing.lg },
  successMessage: { fontSize: 18, fontWeight: '700', color: colors.text.primary },

  // Error
  errorContainer: { alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  errorCircle: { width: 80, height: 80, borderRadius: 40, backgroundColor: colors.health.heart, justifyContent: 'center', alignItems: 'center', marginBottom: spacing.lg },
  errorMessage: { fontSize: 18, fontWeight: '700', color: colors.text.primary },

  // Pulse
  pulseRing: { position: 'absolute' },
  pulseContent: { position: 'absolute' },

  // Wave
  waveContainer: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 4, height: 40 },
  waveBar: { width: 4, borderRadius: 2 },

  // Confetti
  confettiContainer: { ...StyleSheet.absoluteFillObject, zIndex: 9999 },
  confettiPiece: { position: 'absolute', width: 8, height: 8, borderRadius: 2, top: 0 },

  // Floating Input
  floatingInputContainer: { marginBottom: spacing.lg },
  floatingInputWrapper: { borderWidth: 1, borderColor: colors.surface.border, borderRadius: radius.lg, paddingHorizontal: spacing.lg, paddingVertical: spacing.sm, backgroundColor: colors.bg.input },
  floatingInputFocused: { borderColor: colors.primary },
  floatingInputLabel: { position: 'absolute', left: spacing.lg, backgroundColor: colors.bg.input, paddingHorizontal: 4 },
  floatingInput: { height: 48, fontSize: 16, color: colors.text.primary, paddingTop: 12 },
  floatingInputIcon: { position: 'absolute', left: spacing.lg, top: 16, zIndex: 1 },
});
