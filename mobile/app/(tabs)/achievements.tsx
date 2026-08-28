import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet } from 'react-native';
import {
  CheckCircle, Flame, Trophy, Heart, Star, Brain, Smile, Bookmark, MessageCircle,
} from 'lucide-react-native';
import { LoadingScreen, EmptyState } from '../../src/components';
import { API_BASE_URL } from '../../src/services/config';
import { useUserStore } from '../../src/stores';
import { useTheme } from '../../src/services/theme';

const API = API_BASE_URL;

interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  unlocked: boolean;
  progress: number;
  target: number;
}

const ICON_MAP: Record<string, any> = {
  'check-circle': CheckCircle,
  'flame': Flame,
  'trophy': Trophy,
  'heart': Heart,
  'star': Star,
  'brain': Brain,
  'smile': Smile,
  'bookmark': Bookmark,
  'message-circle': MessageCircle,
};

export default function AchievementsScreen() {
  const { theme } = useTheme();
  const userId = useUserStore((s) => s.userId);
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAchievements();
  }, []);

  async function fetchAchievements() {
    try {
      const res = await fetch(`${API}/api/v1/achievements?user_id=${userId}`);
      if (res.ok) {
        setAchievements(await res.json());
      }
    } catch {}
    setLoading(false);
  }

  const unlocked = achievements.filter((a) => a.unlocked).length;
  const total = achievements.length;

  if (loading) return <LoadingScreen />;

  const s = makeStyles(theme);

  return (
    <View style={s.container}>
      <View style={s.header}>
        <Text style={s.title}>Achievements</Text>
        <Text style={s.count}>
          {unlocked}/{total} unlocked
        </Text>
      </View>

      <View style={s.progressBar}>
        <View style={[s.progressFill, { width: `${(unlocked / total) * 100}%` }]} />
      </View>

      <FlatList
        data={achievements}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => {
          const Icon = ICON_MAP[item.icon] || Star;
          return (
            <View style={[s.card, item.unlocked && s.cardUnlocked]}>
              <View style={[s.iconContainer, item.unlocked && s.iconUnlocked]}>
                <Icon size={24} color={item.unlocked ? theme.text : theme.textMuted} />
              </View>
              <View style={s.info}>
                <Text style={[s.name, item.unlocked && s.nameUnlocked]}>
                  {item.name}
                </Text>
                <Text style={s.description}>{item.description}</Text>
                {!item.unlocked && (
                  <View style={s.progressRow}>
                    <View style={s.miniProgress}>
                      <View
                        style={[
                          s.miniProgressFill,
                          { width: `${(item.progress / item.target) * 100}%` },
                        ]}
                      />
                    </View>
                    <Text style={s.progressText}>
                      {item.progress}/{item.target}
                    </Text>
                  </View>
                )}
              </View>
            </View>
          );
        }}
        contentContainerStyle={s.list}
      />
    </View>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.background, padding: 20 },
    header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline', marginTop: 48, marginBottom: 12 },
    title: { fontSize: 28, fontWeight: '700', color: theme.text },
    count: { fontSize: 14, color: theme.textMuted },
    progressBar: { height: 6, backgroundColor: theme.surface, borderRadius: 3, marginBottom: 20 },
    progressFill: { height: 6, backgroundColor: theme.primary, borderRadius: 3 },
    list: { paddingBottom: 40 },
    card: {
      flexDirection: 'row', backgroundColor: theme.surface, borderRadius: 12,
      padding: 16, marginBottom: 8, alignItems: 'center',
    },
    cardUnlocked: { backgroundColor: 'rgba(99, 102, 241, 0.15)', borderWidth: 1, borderColor: theme.primary },
    iconContainer: {
      width: 48, height: 48, borderRadius: 24,
      backgroundColor: theme.surfaceHover, alignItems: 'center', justifyContent: 'center',
      marginRight: 12,
    },
    iconUnlocked: { backgroundColor: theme.primary },
    info: { flex: 1 },
    name: { fontSize: 15, fontWeight: '600', color: theme.textSecondary },
    nameUnlocked: { color: theme.text },
    description: { fontSize: 12, color: theme.textMuted, marginTop: 2 },
    progressRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 6 },
    miniProgress: { flex: 1, height: 4, backgroundColor: theme.surfaceHover, borderRadius: 2 },
    miniProgressFill: { height: 4, backgroundColor: theme.primaryLight, borderRadius: 2 },
    progressText: { fontSize: 11, color: theme.textMuted },
  });
}
