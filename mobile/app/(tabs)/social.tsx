import React, { useEffect, useState } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, TextInput, StyleSheet, Alert,
} from 'react-native';
import { Trophy, Users, TrendingUp, Plus, ChevronRight } from 'lucide-react-native';
import * as Haptics from 'expo-haptics';
import { LoadingScreen } from '../../src/components';
import { API_BASE_URL } from '../../src/services/config';
import { useUserStore } from '../../src/stores';
import { useTheme } from '../../src/services/theme';

const API = API_BASE_URL;

interface Challenge {
  id: string;
  name: string;
  description: string;
  challenge_type: string;
  target_value: number;
  target_unit: string;
  duration_days: number;
  participant_count: number;
  ends_at: string;
  is_active: boolean;
}

interface LeaderboardEntry {
  rank: number;
  user_name: string;
  score: number;
  progress_pct: number;
  is_current_user: boolean;
}

interface Activity {
  id: string;
  user_name: string;
  action: string;
  detail: string;
  timestamp: string;
}

type ViewMode = 'challenges' | 'leaderboard' | 'feed';

const TABS: { key: ViewMode; label: string; icon: any }[] = [
  { key: 'challenges', label: 'Challenges', icon: Trophy },
  { key: 'leaderboard', label: 'Leaderboard', icon: TrendingUp },
  { key: 'feed', label: 'Activity', icon: Users },
];

export default function SocialScreen() {
  const userId = useUserStore((s) => s.userId);
  const { theme } = useTheme();
  const s = makeStyles(theme);
  const [mode, setMode] = useState<ViewMode>('challenges');
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [feed, setFeed] = useState<Activity[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [selectedChallenge, setSelectedChallenge] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (mode === 'challenges') fetchChallenges();
    else if (mode === 'feed') fetchFeed();
    else if (selectedChallenge) fetchLeaderboard();
  }, [mode, selectedChallenge]);

  async function fetchChallenges() {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/social?user_id=${userId}`);
      if (res.ok) setChallenges(await res.json());
    } catch {}
    setLoading(false);
  }

  async function fetchFeed() {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/social/feed`);
      if (ok(res)) setFeed(await res.json());
    } catch {}
    setLoading(false);
  }

  async function fetchLeaderboard() {
    if (!selectedChallenge) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/social/${selectedChallenge}/leaderboard?user_id=${userId}`);
      if (ok(res)) setLeaderboard(await res.json());
    } catch {}
    setLoading(false);
  }

  async function joinChallenge(id: string) {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    try {
      const res = await fetch(`${API}/api/v1/social/${id}/join?user_id=${userId}`, { method: 'POST' });
      if (res.ok) {
        setSelectedChallenge(id);
        setMode('leaderboard');
        fetchChallenges();
      } else if (res.status === 409) {
        setSelectedChallenge(id);
        setMode('leaderboard');
      }
    } catch {}
  }

  async function createChallenge() {
    if (!newName.trim() || !newDesc.trim()) return;
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    try {
      const res = await fetch(`${API}/api/v1/social?user_id=${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newName.trim(), description: newDesc.trim(),
          challenge_type: 'duration', target_value: 30,
          target_unit: 'days', duration_days: 30,
        }),
      });
      if (res.ok) {
        setShowCreate(false);
        setNewName('');
        setNewDesc('');
        fetchChallenges();
      }
    } catch {}
  }

  function daysLeft(endsAt: string) {
    const diff = new Date(endsAt).getTime() - Date.now();
    return Math.max(0, Math.ceil(diff / 86400000));
  }

  if (loading && !showCreate) return <LoadingScreen />;

  return (
    <View style={s.container}>
      <Text style={s.title}>Social</Text>
      <Text style={s.subtitle}>Compete and stay motivated</Text>

      <View style={s.tabs}>
        {TABS.map((t) => {
          const Icon = t.icon;
          const active = mode === t.key;
          return (
            <TouchableOpacity
              key={t.key}
              style={[s.tab, active && s.tabActive]}
              onPress={() => { Haptics.selectionAsync(); setMode(t.key); }}
            >
              <Icon size={16} color={active ? theme.text : theme.textMuted} />
              <Text style={[s.tabText, active && s.tabTextActive]}>{t.label}</Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {mode === 'challenges' && (
        <>
          <TouchableOpacity style={s.createBtn} onPress={() => setShowCreate(!showCreate)}>
            <Plus size={16} color="#0F172A" />
            <Text style={s.createBtnText}>New Challenge</Text>
          </TouchableOpacity>

          {showCreate && (
            <View style={s.createForm}>
              <TextInput style={s.input} value={newName} onChangeText={setNewName}
                placeholder="Challenge name" placeholderTextColor={theme.textMuted} />
              <TextInput style={s.input} value={newDesc} onChangeText={setNewDesc}
                placeholder="Description" placeholderTextColor={theme.textMuted} multiline />
              <TouchableOpacity style={s.submitBtn} onPress={createChallenge}>
                <Text style={s.submitBtnText}>Create</Text>
              </TouchableOpacity>
            </View>
          )}

          <FlatList
            data={challenges}
            keyExtractor={(i) => i.id}
            contentContainerStyle={s.list}
            renderItem={({ item }) => (
              <TouchableOpacity style={s.challengeCard} onPress={() => joinChallenge(item.id)}>
                <View style={s.challengeHeader}>
                  <Text style={s.challengeName}>{item.name}</Text>
                  <ChevronRight size={16} color={theme.textMuted} />
                </View>
                <Text style={s.challengeDesc}>{item.description}</Text>
                <View style={s.challengeMeta}>
                  <Text style={s.metaTag}>{item.target_value} {item.target_unit}</Text>
                  <Text style={s.metaTag}>{item.duration_days}d</Text>
                  <Text style={s.metaTag}>{item.participant_count} joined</Text>
                  <Text style={s.metaTag}>{daysLeft(item.ends_at)}d left</Text>
                </View>
              </TouchableOpacity>
            )}
          />
        </>
      )}

      {mode === 'leaderboard' && (
        <FlatList
          data={leaderboard}
          keyExtractor={(i) => i.user_name}
          contentContainerStyle={s.list}
          ListEmptyComponent={
            <View style={s.empty}>
              <Trophy size={40} color={theme.border} />
              <Text style={s.emptyTitle}>No entries yet</Text>
              <Text style={s.emptyDesc}>Join a challenge to see the leaderboard</Text>
            </View>
          }
          renderItem={({ item }) => (
            <View style={[s.lbRow, item.is_current_user && s.lbRowYou]}>
              <Text style={s.lbRank}>#{item.rank}</Text>
              <View style={s.lbInfo}>
                <Text style={s.lbName}>{item.user_name}{item.is_current_user ? ' (You)' : ''}</Text>
                <View style={s.lbProgressBar}>
                  <View style={[s.lbProgressFill, { width: `${item.progress_pct}%` }]} />
                </View>
              </View>
              <Text style={s.lbScore}>{item.score}</Text>
            </View>
          )}
        />
      )}

      {mode === 'feed' && (
        <FlatList
          data={feed}
          keyExtractor={(i) => i.id}
          contentContainerStyle={s.list}
          renderItem={({ item }) => (
            <View style={s.feedItem}>
              <Text style={s.feedUser}>{item.user_name}</Text>
              <Text style={s.feedAction}> {item.action} </Text>
              <Text style={s.feedDetail}>{item.detail}</Text>
            </View>
          )}
        />
      )}
    </View>
  );
}

function ok(r: Response) { return r.ok; }

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.background, padding: 20 },
    title: { fontSize: 28, fontWeight: '700', color: theme.text, marginTop: 48 },
    subtitle: { fontSize: 14, color: theme.textMuted, marginBottom: 16 },
    tabs: { flexDirection: 'row', gap: 8, marginBottom: 16 },
    tab: {
      flexDirection: 'row', alignItems: 'center', gap: 6,
      paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20,
      backgroundColor: theme.surface,
    },
    tabActive: { backgroundColor: theme.primary },
    tabText: { fontSize: 13, color: theme.textMuted, fontWeight: '500' },
    tabTextActive: { color: theme.text },
    list: { paddingBottom: 40 },
    createBtn: {
      flexDirection: 'row', alignItems: 'center', gap: 8,
      backgroundColor: theme.success, borderRadius: 12,
      padding: 12, marginBottom: 12,
    },
    createBtnText: { color: '#0F172A', fontSize: 14, fontWeight: '600' },
    createForm: { backgroundColor: theme.surface, borderRadius: 12, padding: 16, marginBottom: 12 },
    input: {
      backgroundColor: theme.background, borderRadius: 8, padding: 12,
      fontSize: 14, color: theme.text, marginBottom: 8,
    },
    submitBtn: {
      backgroundColor: theme.primary, borderRadius: 8, padding: 12, alignItems: 'center',
    },
    submitBtnText: { color: '#fff', fontSize: 14, fontWeight: '600' },
    challengeCard: {
      backgroundColor: theme.surface, borderRadius: 12, padding: 16, marginBottom: 8,
    },
    challengeHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
    challengeName: { fontSize: 16, fontWeight: '600', color: theme.text },
    challengeDesc: { fontSize: 13, color: theme.textSecondary, marginTop: 4 },
    challengeMeta: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 10 },
    metaTag: {
      fontSize: 11, color: theme.primaryLight, backgroundColor: theme.primaryBg,
      paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8,
    },
    lbRow: {
      flexDirection: 'row', alignItems: 'center', backgroundColor: theme.surface,
      borderRadius: 12, padding: 14, marginBottom: 8,
    },
    lbRowYou: { borderWidth: 1, borderColor: theme.primary },
    lbRank: { fontSize: 16, fontWeight: '700', color: theme.primaryLight, width: 40 },
    lbInfo: { flex: 1, marginHorizontal: 8 },
    lbName: { fontSize: 14, fontWeight: '500', color: theme.text, marginBottom: 4 },
    lbProgressBar: { height: 4, backgroundColor: theme.surfaceHover, borderRadius: 2 },
    lbProgressFill: { height: 4, backgroundColor: theme.success, borderRadius: 2 },
    lbScore: { fontSize: 14, fontWeight: '600', color: theme.textSecondary },
    feedItem: { flexDirection: 'row', flexWrap: 'wrap', padding: 12, borderBottomWidth: 1, borderBottomColor: theme.surface },
    feedUser: { fontSize: 14, fontWeight: '600', color: theme.primaryLight },
    feedAction: { fontSize: 14, color: theme.textSecondary },
    feedDetail: { fontSize: 14, color: theme.textSecondary },
    empty: { alignItems: 'center', padding: 40 },
    emptyTitle: { fontSize: 18, fontWeight: '600', color: theme.text, marginTop: 12 },
    emptyDesc: { fontSize: 14, color: theme.textMuted, marginTop: 4 },
  });
}
