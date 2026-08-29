/**
 * Toast Notification System — Slide-in Alerts, Quick Feedback
 * Success, error, warning, info toasts with auto-dismiss
 */
import React, { useState, useEffect, useRef, createContext, useContext, useCallback } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, Animated,
  Dimensions, Platform, StatusBar,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../theme';
import * as Haptics from 'expo-haptics';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

type ToastType = 'success' | 'error' | 'warning' | 'info';
type ToastPosition = 'top' | 'bottom';

interface ToastMessage {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
  position?: ToastPosition;
  action?: { label: string; onPress: () => void };
  dismissible?: boolean;
}

interface ToastContextType {
  toast: (msg: Omit<ToastMessage, 'id'>) => void;
  success: (title: string, message?: string) => void;
  error: (title: string, message?: string) => void;
  warning: (title: string, message?: string) => void;
  info: (title: string, message?: string) => void;
  dismiss: () => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

export const useToast = () => {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
};

// ===== TOAST ICONS & COLORS =====
const TOAST_CONFIG: Record<ToastType, { icon: string; color: string; bgColor: string; borderColor: string }> = {
  success: { icon: 'checkmark-circle', color: '#22C55E', bgColor: '#22C55E12', borderColor: '#22C55E30' },
  error: { icon: 'close-circle', color: '#EF4444', bgColor: '#EF444412', borderColor: '#EF444430' },
  warning: { icon: 'warning', color: '#F59E0B', bgColor: '#F59E0B12', borderColor: '#F59E0B30' },
  info: { icon: 'information-circle', color: '#3B82F6', bgColor: '#3B82F612', borderColor: '#3B82F630' },
};

// ===== SINGLE TOAST =====
const ToastItem: React.FC<{
  toast: ToastMessage;
  onDismiss: () => void;
}> = ({ toast: t, onDismiss }) => {
  const slideAnim = useRef(new Animated.Value(t.position === 'bottom' ? 100 : -100)).current;
  const opacityAnim = useRef(new Animated.Value(0)).current;
  const config = TOAST_CONFIG[t.type];

  useEffect(() => {
    // Haptic feedback
    if (t.type === 'success') Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    else if (t.type === 'error') Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    else if (t.type === 'warning') Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
    else Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

    // Slide in
    Animated.parallel([
      Animated.spring(slideAnim, { toValue: 0, useNativeDriver: true, tension: 50, friction: 8 }),
      Animated.timing(opacityAnim, { toValue: 1, duration: 200, useNativeDriver: true }),
    ]).start();

    // Auto dismiss
    const timer = setTimeout(() => {
      Animated.parallel([
        Animated.timing(slideAnim, { toValue: t.position === 'bottom' ? 100 : -100, duration: 250, useNativeDriver: true }),
        Animated.timing(opacityAnim, { toValue: 0, duration: 250, useNativeDriver: true }),
      ]).start(() => onDismiss());
    }, t.duration || 3000);

    return () => clearTimeout(timer);
  }, []);

  return (
    <Animated.View
      style={[
        styles.toastContainer,
        {
          opacity: opacityAnim,
          transform: [{ translateY: slideAnim }],
          [t.position === 'bottom' ? 'bottom' : 'top']: Platform.OS === 'ios' ? 50 : StatusBar.currentHeight ? StatusBar.currentHeight + 10 : 50,
        },
      ]}
    >
      <View style={[styles.toast, { backgroundColor: config.bgColor, borderColor: config.borderColor }]}>
        <View style={[styles.toastIcon, { backgroundColor: config.color + '20' }]}>
          <Ionicons name={config.icon as any} size={18} color={config.color} />
        </View>
        <View style={styles.toastContent}>
          <Text style={styles.toastTitle}>{t.title}</Text>
          {t.message && <Text style={styles.toastMessage}>{t.message}</Text>}
        </View>
        {t.action && (
          <TouchableOpacity onPress={t.action.onPress} style={styles.toastAction}>
            <Text style={[styles.toastActionText, { color: config.color }]}>{t.action.label}</Text>
          </TouchableOpacity>
        )}
        {t.dismissible !== false && (
          <TouchableOpacity onPress={onDismiss} style={styles.toastDismiss}>
            <Ionicons name="close" size={16} color={colors.text.muted} />
          </TouchableOpacity>
        )}
      </View>
    </Animated.View>
  );
};

// ===== TOAST PROVIDER =====
export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const toast = useCallback((msg: Omit<ToastMessage, 'id'>) => {
    const id = Date.now().toString() + Math.random().toString(36).slice(2);
    setToasts(prev => [...prev, { id, ...msg }]);
  }, []);

  const success = useCallback((title: string, message?: string) => toast({ type: 'success', title, message }), [toast]);
  const error = useCallback((title: string, message?: string) => toast({ type: 'error', title, message }), [toast]);
  const warning = useCallback((title: string, message?: string) => toast({ type: 'warning', title, message }), [toast]);
  const info = useCallback((title: string, message?: string) => toast({ type: 'info', title, message }), [toast]);
  const dismiss = useCallback(() => setToasts([]), []);

  const dismissById = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toast, success, error, warning, info, dismiss }}>
      {children}
      {toasts.map(t => (
        <ToastItem key={t.id} toast={t} onDismiss={() => dismissById(t.id)} />
      ))}
    </ToastContext.Provider>
  );
};

// ===== QUICK ALERT =====
interface QuickAlertProps {
  visible: boolean;
  title: string;
  message?: string;
  type?: ToastType;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm?: () => void;
  onCancel?: () => void;
}

export const QuickAlert: React.FC<QuickAlertProps> = ({
  visible, title, message, type = 'info',
  confirmLabel = 'OK', cancelLabel = 'Cancel', onConfirm, onCancel,
}) => {
  const scaleAnim = useRef(new Animated.Value(0.8)).current;
  const opacityAnim = useRef(new Animated.Value(0)).current;
  const config = TOAST_CONFIG[type];

  useEffect(() => {
    if (visible) {
      Animated.parallel([
        Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, tension: 50, friction: 8 }),
        Animated.timing(opacityAnim, { toValue: 1, duration: 200, useNativeDriver: true }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.timing(scaleAnim, { toValue: 0.8, duration: 200, useNativeDriver: true }),
        Animated.timing(opacityAnim, { toValue: 0, duration: 200, useNativeDriver: true }),
      ]).start();
    }
  }, [visible]);

  if (!visible) return null;

  return (
    <Animated.View style={[styles.quickAlertOverlay, { opacity: opacityAnim }]}>
      <Animated.View style={[styles.quickAlert, { transform: [{ scale: scaleAnim }] }]}>
        <View style={[styles.quickAlertIcon, { backgroundColor: config.color + '15' }]}>
          <Ionicons name={config.icon as any} size={32} color={config.color} />
        </View>
        <Text style={styles.quickAlertTitle}>{title}</Text>
        {message && <Text style={styles.quickAlertMessage}>{message}</Text>}
        <View style={styles.quickAlertButtons}>
          {onCancel && (
            <TouchableOpacity style={styles.quickAlertCancelBtn} onPress={onCancel}>
              <Text style={styles.quickAlertCancelText}>{cancelLabel}</Text>
            </TouchableOpacity>
          )}
          <TouchableOpacity
            style={[styles.quickAlertConfirmBtn, { backgroundColor: config.color }]}
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
              onConfirm?.();
            }}
          >
            <Text style={styles.quickAlertConfirmText}>{confirmLabel}</Text>
          </TouchableOpacity>
        </View>
      </Animated.View>
    </Animated.View>
  );
};

// ===== STYLES =====
const styles = StyleSheet.create({
  // Toast
  toastContainer: {
    position: 'absolute', left: spacing.screenPadding, right: spacing.screenPadding,
    zIndex: 9999, elevation: 9999,
  },
  toast: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.md,
    padding: spacing.md, borderRadius: radius.lg,
    borderWidth: 1, ...Platform.select({
      ios: { shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 12 },
      android: { elevation: 8 },
    }),
  },
  toastIcon: { width: 32, height: 32, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  toastContent: { flex: 1 },
  toastTitle: { fontSize: 14, fontWeight: '700', color: colors.text.primary },
  toastMessage: { fontSize: 12, color: colors.text.muted, marginTop: 2 },
  toastAction: { paddingHorizontal: 8, paddingVertical: 4 },
  toastActionText: { fontSize: 13, fontWeight: '700' },
  toastDismiss: { padding: 4 },

  // Quick Alert
  quickAlertOverlay: {
    ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'center', alignItems: 'center', zIndex: 10000,
  },
  quickAlert: {
    width: SCREEN_WIDTH - 64, backgroundColor: colors.bg.card, borderRadius: 24,
    padding: spacing.xl, alignItems: 'center', borderWidth: 1, borderColor: colors.surface.border,
  },
  quickAlertIcon: { width: 64, height: 64, borderRadius: 32, justifyContent: 'center', alignItems: 'center', marginBottom: spacing.lg },
  quickAlertTitle: { fontSize: 18, fontWeight: '700', color: colors.text.primary, textAlign: 'center' },
  quickAlertMessage: { fontSize: 14, color: colors.text.muted, textAlign: 'center', marginTop: spacing.sm, lineHeight: 20 },
  quickAlertButtons: { flexDirection: 'row', gap: spacing.md, marginTop: spacing.xl, width: '100%' },
  quickAlertCancelBtn: { flex: 1, paddingVertical: 14, borderRadius: radius.button, backgroundColor: colors.bg.elevated, alignItems: 'center', borderWidth: 1, borderColor: colors.surface.border },
  quickAlertCancelText: { fontSize: 15, fontWeight: '600', color: colors.text.secondary },
  quickAlertConfirmBtn: { flex: 1, paddingVertical: 14, borderRadius: radius.button, alignItems: 'center' },
  quickAlertConfirmText: { fontSize: 15, fontWeight: '700', color: '#FFF' },
});
