import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Switch, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import * as Haptics from 'expo-haptics';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useTheme, AccentName, CARD_SHADOW } from '../../src/services/theme';
import { api } from '../../src/services/api';
import { useUserStore } from '../../src/stores';
import { LoadingScreen } from '../../src/components';
import { useVisibleItems } from '../../src/components/SectionLanding';
import { MORE } from '../../src/navigation/sections';

interface UserData {
  email: string;
  name: string | null;
  fitness_level: string;
  primary_goal: string;
  preferred_days_per_week: number;
  age?: number | null;
  gender?: string | null;
}

const ACCENT_ORDER: AccentName[] = ['indigo', 'emerald', 'rose', 'amber', 'cyan'];

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
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const moreItems = useVisibleItems(MORE);
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
          {moreItems.map((item) => (
            <SystemRow key={item.route} icon={item.icon} label={item.label} sub={item.sub} color={item.color} theme={theme} onPress={() => router.push(item.route as any)} right={<Ionicons name="chevron-forward" size={16} color={theme.textMuted} />} />
          ))}
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

  list: { borderRadius: 16, borderWidth: 1, overflow: 'hidden' },
  sysRow: { flexDirection: 'row', alignItems: 'center', gap: 12, padding: 14, borderBottomWidth: 1 },
  sysIcon: { width: 34, height: 34, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
  sysLabel: { fontSize: 14, fontWeight: '600' },
  sysSub: { fontSize: 11, marginTop: 2 },
  accentRow: { flexDirection: 'row', gap: 12, padding: 16, paddingTop: 4 },
  swatch: { width: 30, height: 30, borderRadius: 15 },
});
