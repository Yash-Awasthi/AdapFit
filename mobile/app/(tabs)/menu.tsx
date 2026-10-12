import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Switch, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import Animated, { FadeInDown } from 'react-native-reanimated';
import * as Haptics from 'expo-haptics';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useTheme, AccentName, CARD_SHADOW } from '../../src/services/theme';
import { useDevSettings } from '../../src/services/devSettings';
import { useFemaleFeatures } from '../../src/services/gender';
import { useGrid } from '../../src/theme/layout';
import { api } from '../../src/services/api';
import { useUserStore } from '../../src/stores';
import { LoadingScreen } from '../../src/components';

interface UserData {
  email: string;
  name: string | null;
  fitness_level: string;
  primary_goal: string;
  preferred_days_per_week: number;
  age?: number | null;
  gender?: string | null;
}

interface CatalogItem {
  icon: React.ComponentProps<typeof Ionicons>['name'];
  label: string;
  sub: string;
  route: string;
  color: string;
}

interface CatalogSection {
  title: string;
  items: CatalogItem[];
}

function buildCatalog(theme: any, showFemaleScreens: boolean): CatalogSection[] {
  return [
    {
      title: 'Overview',
      items: [
        { icon: 'sunny-outline', label: 'Daily Briefing', sub: "Today's call from your data", route: '/coach', color: '#6366F1' },
        { icon: 'grid-outline', label: 'Dashboard', sub: 'Everything at a glance', route: '/dashboard', color: theme.primary },
        { icon: 'pulse-outline', label: 'Health Hub', sub: 'Vitals & body systems', route: '/health-hub', color: '#22C55E' },
        { icon: 'trending-up', label: 'Trends', sub: 'HRV, load, readiness', route: '/trends', color: '#06B6D4' },
        { icon: 'bar-chart-outline', label: 'Stats', sub: 'Volume & PRs', route: '/stats', color: '#F97316' },
      ],
    },
    {
      title: 'Training',
      items: [
        { icon: 'navigate-outline', label: 'Record a route', sub: 'Run, walk, ride or hike with GPS', route: '/run-record', color: '#22C55E' },
        { icon: 'search', label: 'Exercises', sub: 'Movement library', route: '/exercises', color: theme.primary },
        { icon: 'calendar-outline', label: 'Periodization', sub: 'Long-term plan', route: '/periodization', color: '#06B6D4' },
        { icon: 'ribbon-outline', label: 'Achievements', sub: 'Badges, level & streaks', route: '/achievements', color: '#EAB308' },
        { icon: 'checkbox-outline', label: 'Habits', sub: 'Small daily wins', route: '/habits', color: '#14B8A6' },
        { icon: 'fitness-outline', label: 'Recovery', sub: 'Readiness breakdown', route: '/recovery-dashboard', color: '#EF4444' },
      ],
    },
    {
      title: 'Wellness',
      items: [
        { icon: 'bulb-outline', label: 'Mind', sub: 'Mood, journal & wellbeing', route: '/mental-health', color: '#A855F7' },
        { icon: 'water-outline', label: 'Wellness', sub: 'Hydration, breathing & meditation', route: '/wellness', color: '#06B6D4' },
        { icon: 'leaf-outline', label: 'Everyday Wellbeing', sub: 'Air quality, desk health, memory, travel', route: '/everyday', color: '#22C55E' },
        { icon: 'moon-outline', label: 'Sleep', sub: 'Stages & consistency', route: '/sleep', color: '#6366F1' },
        { icon: 'recording-outline', label: 'Sleep sounds', sub: 'Snoring and noise overnight', route: '/sleep-sounds', color: '#8B5CF6' },
        { icon: 'shield-outline', label: 'Health', sub: 'Conditions & meds', route: '/health', color: '#22C55E' },
        ...(showFemaleScreens
          ? ([
              { icon: 'water-outline', label: 'Cycle', sub: 'Phases & fertility window', route: '/cycle', color: '#EF4444' },
              { icon: 'woman-outline', label: 'Pregnancy', sub: 'Trimester guidance', route: '/pregnancy', color: '#F472B6' },
            ] satisfies CatalogItem[])
          : []),
      ],
    },
    {
      title: 'Nutrition',
      items: [
        { icon: 'restaurant-outline', label: 'Nutrition', sub: 'Meals, macros & photo log', route: '/nutrition', color: '#F59E0B' },
        { icon: 'fast-food-outline', label: 'Recipes', sub: 'Meals that fit macros', route: '/recipes', color: '#F97316' },
        { icon: 'water-outline', label: 'Hydration', sub: 'Daily water intake', route: '/nutrition', color: '#38BDF8' },
      ],
    },
    {
      title: 'Body & Vitals',
      items: [
        { icon: 'scale-outline', label: 'Body', sub: 'Weight, measurements, goals & photos', route: '/body', color: '#F97316' },
        { icon: 'fitness-outline', label: 'Vital Signs', sub: 'Heart rate & blood pressure', route: '/vital-signs', color: '#EF4444' },
        { icon: 'pulse-outline', label: 'HRV', sub: 'Readings & breathing coach', route: '/hrv', color: '#10B981' },
        { icon: 'medical-outline', label: 'Medication', sub: 'Doses & reminders', route: '/medication', color: '#22C55E' },
        { icon: 'watch-outline', label: 'Devices', sub: 'Wearables & sync', route: '/devices', color: '#64748B' },
      ],
    },
    {
      title: 'Community',
      items: [
        { icon: 'heart-circle-outline', label: 'Family', sub: 'Private sharing with people you trust', route: '/family', color: '#EC4899' },
        { icon: 'people-outline', label: 'Community', sub: 'Challenges, leaderboard & feed', route: '/community', color: '#EC4899' },
        { icon: 'chatbubbles-outline', label: 'Forums', sub: 'Ask and answer', route: '/forums', color: '#8B5CF6' },
      ],
    },
    {
      title: 'Tools',
      items: [
        { icon: 'calendar-number-outline', label: 'Calendar', sub: 'Plan and history', route: '/health-calendar', color: '#06B6D4' },
        { icon: 'alarm-outline', label: 'Emergency', sub: 'Contacts & medical ID', route: '/emergency', color: '#DC2626' },
        { icon: 'clipboard-outline', label: 'Conditions & Recovery', sub: 'Check-ups, lab results, physio, falls', route: '/conditions', color: '#0EA5E9' },
        { icon: 'medkit-outline', label: 'Care & Safety', sub: 'Care nearby, symptoms, first aid, schemes', route: '/care', color: '#EF4444' },
        { icon: 'accessibility-outline', label: 'Accessibility', sub: 'Text size & motion', route: '/accessibility-settings', color: '#0EA5E9' },
        { icon: 'download-outline', label: 'Export Data', sub: 'Download your records', route: '/data-export', color: '#22C55E' },
      ],
    },
  ];
}

const ACCENT_ORDER: AccentName[] = ['indigo', 'emerald', 'rose', 'amber', 'cyan'];

function CatalogCard({ item, index, theme, reduceMotion, width }: {
  item: CatalogItem; index: number; theme: any; reduceMotion: boolean; width: number;
}) {
  const router = useRouter();
  const [pressed, setPressed] = useState(false);
  const Icon = item.icon;
  return (
    <Animated.View entering={reduceMotion ? undefined : FadeInDown.duration(280).delay(40 * index)} style={{ width }}>
      <TouchableOpacity
        activeOpacity={0.9}
        onPressIn={() => setPressed(true)}
        onPressOut={() => setPressed(false)}
        onPress={() => { Haptics.selectionAsync(); router.push(item.route as any); }}
        accessibilityRole="button"
        accessibilityLabel={`${item.label}. ${item.sub}`}
        style={[
          styles.card,
          CARD_SHADOW,
          { backgroundColor: theme.surface, borderColor: theme.border, transform: [{ scale: pressed ? 0.97 : 1 }] },
        ]}
      >
        <View style={[styles.cardIcon, { backgroundColor: `${item.color}22` }]}>
          <Ionicons name={Icon} size={20} color={item.color} />
        </View>
        <Text style={[styles.cardLabel, { color: theme.text }]} numberOfLines={1}>{item.label}</Text>
        <Text style={[styles.cardSub, { color: theme.textMuted }]} numberOfLines={2}>{item.sub}</Text>
      </TouchableOpacity>
    </Animated.View>
  );
}

function SystemRow({ icon: Icon, label, sub, color, onPress, right, theme }: any) {
  return (
    <TouchableOpacity style={[styles.sysRow, { borderBottomColor: theme.background }]} onPress={onPress} activeOpacity={onPress ? 0.7 : 1}>
      <View style={[styles.sysIcon, { backgroundColor: `${color}22` }]}>
        <Ionicons name={Icon} size={17} color={color} />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={[styles.sysLabel, { color: theme.text }]}>{label}</Text>
        {!!sub && <Text style={[styles.sysSub, { color: theme.textMuted }]}>{sub}</Text>}
      </View>
      {right}
    </TouchableOpacity>
  );
}

export default function MenuScreen() {
  const { theme, isDark, toggle, accent, setAccent, accents } = useTheme();
  const { reduceMotion } = useDevSettings();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const grid = useGrid(2);
  const showFemaleScreens = useFemaleFeatures();
  const [user, setUser] = useState<UserData | null>(null);
  const [loading, setLoading] = useState(true);
  const profile = useUserStore((s) => s.profile);
  const refreshProfile = useUserStore((s) => s.refreshProfile);

  useEffect(() => {
    const userId = profile?.id || 'default';
    api.getUser(userId).then(setUser).catch(() => {}).finally(() => setLoading(false));
  }, [profile?.id]);

  useEffect(() => {
    refreshProfile();
  }, [refreshProfile]);

  if (loading) return <LoadingScreen />;

  const initials = (user?.name || user?.email || '?').trim().charAt(0).toUpperCase();
  const catalog = buildCatalog(theme, showFemaleScreens);

  return (
    <ScrollView style={{ flex: 1, backgroundColor: theme.background }} contentContainerStyle={{ paddingBottom: 120 }}>
      {/* Profile header */}
      <LinearGradient
        colors={[theme.primary, theme.primaryLight]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={[styles.heroCard, CARD_SHADOW, { paddingTop: insets.top + 20 }]}
      >
        <View style={styles.heroTop}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{initials}</Text>
          </View>
          <TouchableOpacity
            style={styles.editBtn}
            onPress={() => { Haptics.selectionAsync(); router.push('/personal-info' as any); }}
          >
            <Ionicons name="pencil-outline" size={14} color="#fff" />
            <Text style={styles.editBtnText}>Edit</Text>
          </TouchableOpacity>
        </View>
        <Text style={styles.heroName}>{user?.name || 'Your Profile'}</Text>
        <Text style={styles.heroEmail}>{user?.email || ''}</Text>
        <View style={styles.heroTags}>
          {user?.age ? <View style={styles.heroTag}><Text style={styles.heroTagText}>{user.age}y</Text></View> : null}
          {user?.gender ? <View style={styles.heroTag}><Text style={styles.heroTagText}>{user.gender.replace('_', ' ')}</Text></View> : null}
          {user?.fitness_level ? <View style={styles.heroTag}><Text style={styles.heroTagText}>{user.fitness_level}</Text></View> : null}
          {user?.primary_goal ? <View style={styles.heroTag}><Text style={styles.heroTagText}>{user.primary_goal.replace('_', ' ')}</Text></View> : null}
        </View>
      </LinearGradient>

      {/* Catalog */}
      {catalog.map((section) => (
        <View key={section.title} style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>{section.title}</Text>
          <View style={[styles.grid, { gap: grid.gap }]}>
            {section.items.map((item, i) => (
              <CatalogCard
                key={item.label}
                item={item}
                index={i}
                theme={theme}
                reduceMotion={reduceMotion}
                width={grid.cell}
              />
            ))}
          </View>
        </View>
      ))}

      {/* Appearance */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>Appearance</Text>
        <View style={[styles.list, CARD_SHADOW, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <SystemRow
            icon={isDark ? 'moon-outline' : 'sunny-outline'}
            label="Dark mode"
            sub={isDark ? 'On' : 'Off'}
            color={theme.primary}
            theme={theme}
            right={
              <Switch
                value={isDark}
                onValueChange={() => { Haptics.selectionAsync(); toggle(); }}
                trackColor={{ false: theme.border, true: theme.primary }}
                thumbColor="#fff"
              />
            }
          />
          <View style={styles.accentRow}>
            {ACCENT_ORDER.map((name) => (
              <TouchableOpacity
                key={name}
                accessibilityRole="radio"
                accessibilityLabel={`${name} accent`}
                onPress={() => { Haptics.selectionAsync(); setAccent(name); }}
                style={[
                  styles.swatch,
                  { backgroundColor: accents[name].primary },
                  accent === name && { borderWidth: 3, borderColor: theme.text },
                ]}
              />
            ))}
          </View>
        </View>
      </View>

      {/* Account & system */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>Account</Text>
        <View style={[styles.list, CARD_SHADOW, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <SystemRow icon="resize-outline" label="Body & measurements" sub="Age, height, training preferences" color="#38BDF8" theme={theme} onPress={() => router.push('/personal-info' as any)} right={<Ionicons name="chevron-forward" size={16} color={theme.textMuted} />} />
          {__DEV__ && <SystemRow icon="construct-outline" label="Dev Tools" sub="Your own AI key, reduce motion" color="#94A3B8" theme={theme} onPress={() => router.push('/dev-tools' as any)} right={<Ionicons name="chevron-forward" size={16} color={theme.textMuted} />} />}
          <SystemRow icon="settings-outline" label="App preferences" sub="Notifications, reminders" color="#818CF8" theme={theme} onPress={() => router.push('/settings' as any)} right={<Ionicons name="chevron-forward" size={16} color={theme.textMuted} />} />
          <SystemRow icon="notifications-outline" label="Notifications" sub="Manage alerts" color="#F59E0B" theme={theme} onPress={() => router.push('/settings' as any)} right={<Ionicons name="chevron-forward" size={16} color={theme.textMuted} />} />
          <SystemRow icon="information-circle-outline" label="About AdapFit" sub="v2.0 — AI-powered adaptive fitness" color="#06B6D4" theme={theme} />
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  heroCard: { margin: 16, borderRadius: 20, padding: 20, paddingTop: 60 },
  heroTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  avatar: {
    width: 56, height: 56, borderRadius: 28, backgroundColor: 'rgba(255,255,255,0.25)',
    alignItems: 'center', justifyContent: 'center',
  },
  avatarText: { fontSize: 24, fontWeight: '800', color: '#fff' },
  editBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: 'rgba(255,255,255,0.2)', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16,
  },
  editBtnText: { color: '#fff', fontSize: 12, fontWeight: '700' },
  heroName: { fontSize: 22, fontWeight: '800', color: '#fff', marginTop: 16 },
  heroEmail: { fontSize: 13, color: 'rgba(255,255,255,0.85)', marginTop: 2 },
  heroTags: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 14 },
  heroTag: { backgroundColor: 'rgba(255,255,255,0.2)', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 10 },
  heroTagText: { color: '#fff', fontSize: 11, fontWeight: '600', textTransform: 'capitalize' },

  section: { paddingHorizontal: 20, marginTop: 8, marginBottom: 8 },
  sectionTitle: { fontSize: 13, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.6, marginBottom: 10 },
  grid: { flexDirection: 'row', flexWrap: 'wrap' },
  // Fixed height so a one-line and a two-line subtitle keep the same card box.
  card: { height: 122, borderRadius: 16, borderWidth: 1, padding: 14, gap: 2 },
  cardIcon: { width: 36, height: 36, borderRadius: 10, alignItems: 'center', justifyContent: 'center', marginBottom: 6 },
  cardLabel: { fontSize: 14, fontWeight: '700' },
  cardSub: { fontSize: 11, lineHeight: 15 },

  list: { borderRadius: 16, borderWidth: 1, overflow: 'hidden' },
  sysRow: { flexDirection: 'row', alignItems: 'center', gap: 12, padding: 14, borderBottomWidth: 1 },
  sysIcon: { width: 34, height: 34, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
  sysLabel: { fontSize: 14, fontWeight: '600' },
  sysSub: { fontSize: 11, marginTop: 2 },
  accentRow: { flexDirection: 'row', gap: 12, padding: 16, paddingTop: 4 },
  swatch: { width: 30, height: 30, borderRadius: 15 },
});
