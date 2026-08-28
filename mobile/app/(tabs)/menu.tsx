import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Switch, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import Animated, { FadeInDown } from 'react-native-reanimated';
import * as Haptics from 'expo-haptics';
import {
  ChevronRight, Sun, Moon as MoonIcon, Search, Calendar, BarChart3, Award,
  Brain, Moon, Shield, Utensils, Salad, Users, Settings as SettingsIcon,
  Download, Bell, Info, Pencil, Ruler, Droplet, Wrench,
} from 'lucide-react-native';
import { useTheme, AccentName, CARD_SHADOW } from '../../src/services/theme';
import { useDevSettings } from '../../src/services/devSettings';
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
  icon: any;
  label: string;
  sub: string;
  route: string;
  color: string;
}

interface CatalogSection {
  title: string;
  items: CatalogItem[];
}

function buildCatalog(theme: any, showCycle: boolean): CatalogSection[] {
  return [
    {
      title: 'Training',
      items: [
        { icon: Search, label: 'Exercises', sub: 'Movement library', route: '/exercises', color: theme.primary },
        { icon: Calendar, label: 'Periodization', sub: 'Long-term plan', route: '/periodization', color: '#06B6D4' },
        { icon: BarChart3, label: 'Stats', sub: 'Volume & PRs', route: '/stats', color: '#F97316' },
        { icon: Award, label: 'Achievements', sub: '25 badges to earn', route: '/achievements', color: '#EAB308' },
      ],
    },
    {
      title: 'Wellness',
      items: [
        { icon: Brain, label: 'Wellness', sub: 'Mood & mind check-in', route: '/wellness', color: '#A855F7' },
        { icon: Moon, label: 'Sleep', sub: 'Stages & consistency', route: '/sleep', color: '#6366F1' },
        { icon: Shield, label: 'Health', sub: 'Conditions & meds', route: '/health', color: '#22C55E' },
        ...(showCycle
          ? [{ icon: Droplet, label: 'Cycle', sub: 'Phase-aware training', route: '/cycle', color: '#EF4444' }]
          : []),
      ],
    },
    {
      title: 'Nutrition',
      items: [
        { icon: Utensils, label: 'Nutrition', sub: 'Macros & meal plans', route: '/nutrition', color: '#F59E0B' },
        { icon: Salad, label: 'Diet Log', sub: 'Quick meal logging', route: '/diet', color: '#84CC16' },
      ],
    },
    {
      title: 'Community',
      items: [
        { icon: Users, label: 'Social', sub: 'Feed & challenges', route: '/social', color: '#EC4899' },
      ],
    },
  ];
}

const ACCENT_ORDER: AccentName[] = ['indigo', 'emerald', 'rose', 'amber', 'cyan'];

function CatalogCard({ item, index, theme, reduceMotion }: { item: CatalogItem; index: number; theme: any; reduceMotion: boolean }) {
  const router = useRouter();
  const [pressed, setPressed] = useState(false);
  const Icon = item.icon;
  return (
    <Animated.View entering={reduceMotion ? undefined : FadeInDown.duration(280).delay(40 * index)} style={styles.cardWrap}>
      <TouchableOpacity
        activeOpacity={0.9}
        onPressIn={() => setPressed(true)}
        onPressOut={() => setPressed(false)}
        onPress={() => { Haptics.selectionAsync(); router.push(item.route as any); }}
        style={[
          styles.card,
          CARD_SHADOW,
          { backgroundColor: theme.surface, borderColor: theme.border, transform: [{ scale: pressed ? 0.97 : 1 }] },
        ]}
      >
        <View style={[styles.cardIcon, { backgroundColor: `${item.color}22` }]}>
          <Icon size={20} color={item.color} />
        </View>
        <Text style={[styles.cardLabel, { color: theme.text }]}>{item.label}</Text>
        <Text style={[styles.cardSub, { color: theme.textMuted }]} numberOfLines={1}>{item.sub}</Text>
      </TouchableOpacity>
    </Animated.View>
  );
}

function SystemRow({ icon: Icon, label, sub, color, onPress, right, theme }: any) {
  return (
    <TouchableOpacity style={[styles.sysRow, { borderBottomColor: theme.background }]} onPress={onPress} activeOpacity={onPress ? 0.7 : 1}>
      <View style={[styles.sysIcon, { backgroundColor: `${color}22` }]}>
        <Icon size={17} color={color} />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={[styles.sysLabel, { color: theme.text }]}>{label}</Text>
        {sub && <Text style={[styles.sysSub, { color: theme.textMuted }]}>{sub}</Text>}
      </View>
      {right}
    </TouchableOpacity>
  );
}

export default function MenuScreen() {
  const { theme, isDark, toggle, accent, setAccent, accents } = useTheme();
  const { reduceMotion } = useDevSettings();
  const router = useRouter();
  const [user, setUser] = useState<UserData | null>(null);
  const [loading, setLoading] = useState(true);
  const profile = useUserStore((s) => s.profile);
  const hydrated = useUserStore((s) => s.hydrated);
  const refreshProfile = useUserStore((s) => s.refreshProfile);

  useEffect(() => {
    const userId = profile?.id || 'default';
    api.getUser(userId).then(setUser).catch(() => {}).finally(() => setLoading(false));
  }, [profile?.id, profile?.gender]);

  useEffect(() => {
    refreshProfile();
  }, []);

  if (loading) return <LoadingScreen />;

  const showCycle = hydrated && profile?.gender === 'female';
  const initials = (user?.name || user?.email || '?').trim().charAt(0).toUpperCase();
  const catalog = buildCatalog(theme, showCycle);

  return (
    <ScrollView style={{ flex: 1, backgroundColor: theme.background }} contentContainerStyle={{ paddingBottom: 100 }}>
      {/* Profile header */}
      <LinearGradient
        colors={[theme.primary, theme.primaryLight]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={[styles.heroCard, CARD_SHADOW]}
      >
        <View style={styles.heroTop}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{initials}</Text>
          </View>
          <TouchableOpacity
            style={styles.editBtn}
            onPress={() => { Haptics.selectionAsync(); router.push('/personal-info' as any); }}
          >
            <Pencil size={14} color="#fff" />
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
          <View style={styles.grid}>
            {section.items.map((item, i) => (
              <CatalogCard key={item.label} item={item} index={i} theme={theme} reduceMotion={reduceMotion} />
            ))}
          </View>
        </View>
      ))}

      {/* Appearance */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>Appearance</Text>
        <View style={[styles.list, CARD_SHADOW, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <SystemRow
            icon={isDark ? MoonIcon : Sun}
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
          <SystemRow icon={Ruler} label="Body & system status" sub="Measurements, backend health" color="#38BDF8" theme={theme} onPress={() => router.push('/profile' as any)} right={<ChevronRight size={16} color={theme.textMuted} />} />
          <SystemRow icon={Wrench} label="Dev Tools" sub="Your own AI key, reduce motion" color="#94A3B8" theme={theme} onPress={() => router.push('/dev-tools' as any)} right={<ChevronRight size={16} color={theme.textMuted} />} />
          <SystemRow icon={SettingsIcon} label="App preferences" sub="Notifications, reminders" color="#818CF8" theme={theme} onPress={() => router.push('/settings' as any)} right={<ChevronRight size={16} color={theme.textMuted} />} />
          <SystemRow icon={Bell} label="Notifications" sub="Manage alerts" color="#F59E0B" theme={theme} onPress={() => router.push('/settings' as any)} right={<ChevronRight size={16} color={theme.textMuted} />} />
          <SystemRow
            icon={Download}
            label="Export my data"
            sub="JSON download"
            color="#22C55E"
            theme={theme}
            onPress={() => Alert.alert('Export started', 'Your data export will be ready shortly.')}
            right={<ChevronRight size={16} color={theme.textMuted} />}
          />
          <SystemRow icon={Info} label="About AdapFit" sub="v2.0 — AI-powered adaptive fitness" color="#06B6D4" theme={theme} />
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

  section: { paddingHorizontal: 16, marginTop: 8, marginBottom: 8 },
  sectionTitle: { fontSize: 13, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.6, marginBottom: 10 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  cardWrap: { width: '47%' },
  card: { borderRadius: 16, borderWidth: 1, padding: 14, gap: 4 },
  cardIcon: { width: 36, height: 36, borderRadius: 10, alignItems: 'center', justifyContent: 'center', marginBottom: 6 },
  cardLabel: { fontSize: 14, fontWeight: '700' },
  cardSub: { fontSize: 11 },

  list: { borderRadius: 16, borderWidth: 1, overflow: 'hidden' },
  sysRow: { flexDirection: 'row', alignItems: 'center', gap: 12, padding: 14, borderBottomWidth: 1 },
  sysIcon: { width: 34, height: 34, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
  sysLabel: { fontSize: 14, fontWeight: '600' },
  sysSub: { fontSize: 11, marginTop: 2 },
  accentRow: { flexDirection: 'row', gap: 12, padding: 16, paddingTop: 4 },
  swatch: { width: 30, height: 30, borderRadius: 15 },
});
