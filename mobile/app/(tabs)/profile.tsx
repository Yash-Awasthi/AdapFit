/**
 * Profile Screen — Premium User Profile & Settings
 * Glassmorphism cards, avatar, stats, settings shortcuts
 */
import React, { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Switch, Dimensions,
} from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, glass } from '../../src/theme';
import { GlassCard, SectionHeaderPremium, ScoreRing, StatCard } from '../../src/components/PremiumComponents';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

export default function ProfileScreen() {
  const router = useRouter();
  const [darkMode, setDarkMode] = useState(true);
  const [notifications, setNotifications] = useState(true);

  const userStats = [
    { value: '28', label: 'Age', icon: 'person', color: colors.primary },
    { value: '72', label: 'Health Score', icon: 'heart', color: colors.health.heart },
    { value: '5', label: 'Day Streak', icon: 'flame', color: colors.health.energy },
    { value: '12', label: 'Workouts', icon: 'barbell', color: colors.health.activity },
  ];

  const menuItems = [
    { icon: 'person', label: 'Personal Info', color: colors.primary, route: '/personal-info' },
    { icon: 'fitness', label: 'Health Goals', color: colors.health.calm, route: '/health-hub' },
    { icon: 'notifications', label: 'Notifications', color: '#F59E0B', route: '/settings' },
    { icon: 'shield-checkmark', label: 'Privacy & Security', color: colors.health.heart, route: '/settings' },
    { icon: 'download', label: 'Export Health Data', color: colors.health.activity, route: '/data-export' },
    { icon: 'phone-portrait', label: 'Connected Devices', color: colors.health.sleep, route: '/devices' },
    { icon: 'accessibility', label: 'Accessibility', color: colors.health.mental, route: '/accessibility-settings' },
    { icon: 'language', label: 'Language', color: '#06B6D4', route: '/settings' },
    { icon: 'help-circle', label: 'Help & Support', color: colors.health.calm, route: '/settings' },
    { icon: 'information-circle', label: 'About AdapFit', color: colors.text.muted, route: '/settings' },
  ];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* Header with Avatar */}
      <LinearGradient colors={['#6366F1', '#8B5CF6']} style={styles.header}>
        <View style={styles.avatarContainer}>
          <View style={styles.avatar}>
            <Ionicons name="person" size={32} color="#FFF" />
          </View>
          <View style={styles.onlineIndicator} />
        </View>
        <Text style={styles.userName}>Alex Johnson</Text>
        <Text style={styles.userEmail}>alex@adapfit.com</Text>
        <Text style={styles.memberSince}>Member since Jan 2024</Text>
      </LinearGradient>

      {/* Health Score Card */}
      <View style={styles.scoreSection}>
        <GlassCard variant="light" style={styles.scoreCard}>
          <View style={styles.scoreRow}>
            <ScoreRing score={72} size={90} strokeWidth={6} color={colors.score.good} label="HEALTH" />
            <View style={styles.scoreDetails}>
              <Text style={styles.scoreTitle}>Health Score</Text>
              <Text style={styles.scoreSubtitle}>Good — Keep improving!</Text>
              <View style={styles.scoreBreakdown}>
                <View style={styles.scoreItem}>
                  <View style={[styles.scoreDot, { backgroundColor: colors.health.heart }]} />
                  <Text style={styles.scoreItemText}>Heart: 85</Text>
                </View>
                <View style={styles.scoreItem}>
                  <View style={[styles.scoreDot, { backgroundColor: colors.health.sleep }]} />
                  <Text style={styles.scoreItemText}>Sleep: 78</Text>
                </View>
                <View style={styles.scoreItem}>
                  <View style={[styles.scoreDot, { backgroundColor: colors.health.activity }]} />
                  <Text style={styles.scoreItemText}>Activity: 72</Text>
                </View>
              </View>
            </View>
          </View>
        </GlassCard>
      </View>

      {/* Stats Grid */}
      <View style={styles.statsGrid}>
        {userStats.map((stat, i) => (
          <StatCard key={i} value={stat.value} label={stat.label} icon={stat.icon} color={stat.color} />
        ))}
      </View>

      {/* Settings Menu */}
      <SectionHeaderPremium icon="settings" iconColor={colors.primary} title="Settings" />
      <View style={styles.menuContainer}>
        {menuItems.map((item, i) => (
          <TouchableOpacity
            key={i}
            style={styles.menuItem}
            onPress={() => router.push(item.route as any)}
          >
            <View style={[styles.menuIcon, { backgroundColor: item.color + '15' }]}>
              <Ionicons name={item.icon as any} size={18} color={item.color} />
            </View>
            <Text style={styles.menuLabel}>{item.label}</Text>
            <Ionicons name="chevron-forward" size={16} color={colors.text.muted} />
          </TouchableOpacity>
        ))}
      </View>

      {/* Quick Toggles */}
      <SectionHeaderPremium icon="toggle-left" iconColor={colors.health.calm} title="Quick Settings" />
      <GlassCard variant="light" style={styles.togglesCard}>
        <View style={styles.toggleRow}>
          <View style={styles.toggleInfo}>
            <Ionicons name="moon" size={18} color={colors.health.sleep} />
            <Text style={styles.toggleLabel}>Dark Mode</Text>
          </View>
          <Switch
            value={darkMode}
            onValueChange={setDarkMode}
            trackColor={{ false: colors.surface.divider, true: colors.primary + '60' }}
            thumbColor={darkMode ? colors.primary : colors.text.muted}
          />
        </View>
        <View style={styles.toggleDivider} />
        <View style={styles.toggleRow}>
          <View style={styles.toggleInfo}>
            <Ionicons name="notifications" size={18} color="#F59E0B" />
            <Text style={styles.toggleLabel}>Push Notifications</Text>
          </View>
          <Switch
            value={notifications}
            onValueChange={setNotifications}
            trackColor={{ false: colors.surface.divider, true: colors.primary + '60' }}
            thumbColor={notifications ? colors.primary : colors.text.muted}
          />
        </View>
      </GlassCard>

      {/* Logout */}
      <TouchableOpacity style={styles.logoutBtn}>
        <Ionicons name="log-out" size={18} color={colors.health.danger} />
        <Text style={styles.logoutText}>Sign Out</Text>
      </TouchableOpacity>

      <Text style={styles.version}>AdapFit v2.0.0 • Built with 💜</Text>

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  contentContainer: { paddingBottom: 100 },

  // Header
  header: { paddingTop: 56, paddingBottom: spacing.xl, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 28, borderBottomRightRadius: 28, alignItems: 'center' },
  avatarContainer: { position: 'relative', marginBottom: spacing.md },
  avatar: { width: 72, height: 72, borderRadius: 36, backgroundColor: 'rgba(255,255,255,0.2)', justifyContent: 'center', alignItems: 'center' },
  onlineIndicator: { position: 'absolute', bottom: 2, right: 2, width: 14, height: 14, borderRadius: 7, backgroundColor: colors.health.calm, borderWidth: 2, borderColor: colors.primary },
  userName: { fontSize: 22, fontWeight: '800', color: '#FFF' },
  userEmail: { fontSize: 14, color: 'rgba(255,255,255,0.7)', marginTop: 2 },
  memberSince: { fontSize: 12, color: 'rgba(255,255,255,0.5)', marginTop: 4 },

  // Score
  scoreSection: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.lg },
  scoreCard: {},
  scoreRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.xl },
  scoreDetails: { flex: 1 },
  scoreTitle: { fontSize: 16, fontWeight: '700', color: colors.text.primary },
  scoreSubtitle: { fontSize: 13, color: colors.text.muted, marginTop: 2 },
  scoreBreakdown: { flexDirection: 'row', gap: spacing.md, marginTop: spacing.md },
  scoreItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  scoreDot: { width: 6, height: 6, borderRadius: 3 },
  scoreItemText: { fontSize: 11, color: colors.text.muted },

  // Stats
  statsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md, paddingHorizontal: spacing.screenPadding, marginTop: spacing.lg },

  // Menu
  menuContainer: { paddingHorizontal: spacing.screenPadding },
  menuItem: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.md,
    backgroundColor: colors.bg.card, padding: spacing.lg,
    borderRadius: radius.lg, marginBottom: spacing.sm,
    borderWidth: 1, borderColor: colors.surface.border,
  },
  menuIcon: { width: 36, height: 36, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  menuLabel: { flex: 1, fontSize: 15, fontWeight: '600', color: colors.text.primary },

  // Toggles
  togglesCard: { marginHorizontal: spacing.screenPadding },
  toggleRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: spacing.sm },
  toggleInfo: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  toggleLabel: { fontSize: 15, fontWeight: '500', color: colors.text.primary },
  toggleDivider: { height: 1, backgroundColor: colors.surface.divider, marginVertical: spacing.sm },

  // Logout
  logoutBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.sm,
    marginHorizontal: spacing.screenPadding, marginTop: spacing.xl,
    backgroundColor: colors.health.dangerBg, padding: spacing.lg, borderRadius: radius.lg,
    borderWidth: 1, borderColor: colors.health.danger + '30',
  },
  logoutText: { fontSize: 15, fontWeight: '600', color: colors.health.danger },

  // Version
  version: { fontSize: 12, color: colors.text.muted, textAlign: 'center', marginTop: spacing.xl },
});
