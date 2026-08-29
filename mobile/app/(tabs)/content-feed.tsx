/**
 * Content Hub — video and GIF feed for health and training content.
 */
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet,
  RefreshControl, TextInput, ActivityIndicator, Linking,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../../src/theme';
import { useGrid } from '../../src/theme/layout';
import { VideoCard, inlinePlaybackAvailable } from '../../src/components/VideoCard';
import { getJson, asArray } from '../../src/services/http';

interface YouTubeHit {
  video_id: string;
  title: string;
  channel: string;
  duration_seconds: number;
  view_count: number;
  thumbnail_url: string;
  watch_url: string;
  embed_url: string;
}

interface Item {
  id: string;
  title: string;
  description: string;
  content_type: string;
  category: string;
  difficulty: string;
  duration_seconds: number;
  rating: number;
  view_count: number;
  muscles_targeted: string[];
  video_id?: string | null;
  thumbnail_url?: string | null;
  embed_url?: string | null;
  watch_url?: string | null;
  search_url?: string | null;
  gif_url?: string | null;
}

const CATEGORIES = [
  { label: 'All', value: 'all', icon: 'apps', color: colors.primary },
  { label: 'Strength', value: 'strength', icon: 'barbell', color: colors.health.heart },
  { label: 'Cardio', value: 'cardio', icon: 'walk', color: colors.health.activity },
  { label: 'Mental', value: 'mental_wellness', icon: 'leaf', color: colors.health.mental },
  { label: 'Nutrition', value: 'nutrition', icon: 'restaurant', color: colors.health.nutrition },
  { label: 'Sleep', value: 'sleep', icon: 'moon', color: colors.health.sleep },
  { label: 'Flexibility', value: 'flexibility', icon: 'body', color: colors.health.stress },
];

const TYPE_STYLE: Record<string, { accent: string; icon: string; label: string }> = {
  exercise_video: { accent: colors.health.heart, icon: 'barbell', label: 'Exercise' },
  exercise_gif: { accent: colors.health.energy, icon: 'body', label: 'Demo' },
  meditation: { accent: colors.health.mental, icon: 'leaf', label: 'Meditation' },
  nutrition_tip: { accent: colors.health.nutrition, icon: 'restaurant', label: 'Nutrition' },
  article: { accent: colors.health.activity, icon: 'document-text', label: 'Read' },
  sleep_education: { accent: colors.health.sleep, icon: 'moon', label: 'Sleep' },
};

const DIFFICULTY_COLOR: Record<string, string> = {
  beginner: colors.health.calm,
  intermediate: colors.health.stress,
  advanced: colors.health.heart,
  all_levels: colors.text.muted,
};

const FALLBACK: Item[] = [
  {
    id: 'fb-1', title: 'Barbell Back Squat — Proper Form Guide',
    description: 'Bracing, bar path, and depth, plus the mistakes that cost you the lift.',
    content_type: 'exercise_video', category: 'strength', difficulty: 'all_levels',
    duration_seconds: 720, rating: 4.8, view_count: 12400,
    muscles_targeted: ['Quads', 'Glutes', 'Core'],
    video_id: 'bEv6CCg2BC8',
    thumbnail_url: 'https://img.youtube.com/vi/bEv6CCg2BC8/hqdefault.jpg',
    embed_url: 'https://www.youtube-nocookie.com/embed/bEv6CCg2BC8?rel=0&playsinline=1',
    watch_url: 'https://www.youtube.com/watch?v=bEv6CCg2BC8',
  },
  {
    id: 'fb-2', title: 'The Five Lifts — Squat, Deadlift, Bench, Press, Row',
    description: 'One walkthrough covering setup and execution for each main barbell lift.',
    content_type: 'exercise_video', category: 'strength', difficulty: 'beginner',
    duration_seconds: 900, rating: 4.7, view_count: 15600,
    muscles_targeted: ['Full body'],
    video_id: 'DQGHPLs9N6Y',
    thumbnail_url: 'https://img.youtube.com/vi/DQGHPLs9N6Y/hqdefault.jpg',
    embed_url: 'https://www.youtube-nocookie.com/embed/DQGHPLs9N6Y?rel=0&playsinline=1',
    watch_url: 'https://www.youtube.com/watch?v=DQGHPLs9N6Y',
  },
  {
    id: 'fb-3', title: 'Box Breathing for Stress Relief',
    description: 'A four-count cycle you can run in under five minutes to drop arousal.',
    content_type: 'meditation', category: 'mental_wellness', difficulty: 'beginner',
    duration_seconds: 300, rating: 4.6, view_count: 7800, muscles_targeted: [],
    search_url: 'https://www.youtube.com/results?search_query=box+breathing+for+stress+relief',
  },
  {
    id: 'fb-4', title: 'HRV — Your Recovery Dashboard',
    description: 'Why heart rate variability tracks readiness better than resting heart rate alone.',
    content_type: 'article', category: 'general_health', difficulty: 'intermediate',
    duration_seconds: 480, rating: 4.8, view_count: 3800, muscles_targeted: [],
    search_url: 'https://www.youtube.com/results?search_query=heart+rate+variability+recovery+explained',
  },
];

function formatViews(count: number): string {
  if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(1)}M`;
  if (count >= 1_000) return `${(count / 1_000).toFixed(1)}K`;
  return String(count);
}

function ContentCard({ item, width }: { item: Item; width: number }) {
  const style = TYPE_STYLE[item.content_type] || {
    accent: colors.primary, icon: 'document-text', label: 'Content',
  };
  const difficultyColor = DIFFICULTY_COLOR[item.difficulty] || colors.text.muted;

  return (
    <View style={[styles.card, { width }]}>
      <VideoCard
        title={item.title}
        videoId={item.video_id}
        thumbnailUrl={item.thumbnail_url}
        embedUrl={item.embed_url}
        watchUrl={item.watch_url}
        searchUrl={item.search_url}
        gifUrl={item.gif_url}
        accent={style.accent}
        icon={style.icon}
        durationSeconds={item.duration_seconds}
        height={Math.round(width * 0.5625)}
      />

      <View style={styles.cardBody}>
        <View style={styles.cardTopRow}>
          <View style={[styles.typeTag, { backgroundColor: style.accent + '22' }]}>
            <Ionicons name={style.icon as any} size={11} color={style.accent} />
            <Text style={[styles.typeTagText, { color: style.accent }]}>{style.label}</Text>
          </View>
          {item.rating > 0 && (
            <View style={styles.ratingRow}>
              <Ionicons name="star" size={12} color={colors.health.stress} />
              <Text style={styles.ratingText}>{item.rating.toFixed(1)}</Text>
            </View>
          )}
        </View>

        <Text style={styles.cardTitle} numberOfLines={2}>{item.title}</Text>
        {!!item.description && (
          <View style={styles.channelRow}>
            <Ionicons name="person-circle-outline" size={13} color={colors.text.muted} />
            <Text style={styles.cardDescription} numberOfLines={1}>{item.description}</Text>
          </View>
        )}

        <View style={styles.cardFooter}>
          {item.view_count > 0 ? (
            <View style={styles.footerItem}>
              <Ionicons name="eye-outline" size={12} color={colors.text.muted} />
              <Text style={styles.footerText}>{formatViews(item.view_count)} views</Text>
            </View>
          ) : (
            <View style={styles.footerItem}>
              <Ionicons name="logo-youtube" size={12} color={colors.text.muted} />
              <Text style={styles.footerText}>YouTube</Text>
            </View>
          )}
          <View style={[styles.difficultyBadge, { backgroundColor: difficultyColor + '1F' }]}>
            <Text style={[styles.difficultyText, { color: difficultyColor }]}>
              {item.difficulty.replace(/_/g, ' ')}
            </Text>
          </View>
        </View>

        {item.muscles_targeted?.length > 0 && (
          <View style={styles.muscleRow}>
            {item.muscles_targeted.slice(0, 3).map((m) => (
              <View key={m} style={styles.muscleTag}>
                <Text style={styles.muscleText} numberOfLines={1}>{m}</Text>
              </View>
            ))}
          </View>
        )}
      </View>
    </View>
  );
}

/** Map a YouTube search hit onto the card model the feed renders. */
function fromYouTube(hit: YouTubeHit, category: string): Item {
  return {
    id: hit.video_id,
    title: hit.title,
    description: hit.channel,
    content_type: 'exercise_video',
    category,
    difficulty: 'all_levels',
    duration_seconds: hit.duration_seconds,
    rating: 0,
    view_count: hit.view_count,
    muscles_targeted: [],
    video_id: hit.video_id,
    thumbnail_url: hit.thumbnail_url,
    embed_url: hit.embed_url,
    watch_url: hit.watch_url,
  };
}

export default function ContentFeedScreen() {
  const insets = useSafeAreaInsets();
  const grid = useGrid(1, spacing.lg);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState('all');
  const [content, setContent] = useState<Item[]>([]);
  const [search, setSearch] = useState('');
  const [query, setQuery] = useState('');

  const fetchData = useCallback(async () => {
    const path = query
      ? `/content/youtube/search?q=${encodeURIComponent(query)}&limit=20`
      : `/content/youtube/category/${category}?limit=20`;
    const data = await getJson<{ results: YouTubeHit[] }>(path);
    const hits = asArray<YouTubeHit>(data?.results);
    setContent(hits.length ? hits.map((h) => fromYouTube(h, category)) : FALLBACK);
    setLoading(false);
  }, [category, query]);

  useEffect(() => {
    setLoading(true);
    fetchData();
  }, [fetchData]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  }, [fetchData]);

  // Submitting is what runs a search: each one costs a YouTube extraction on
  // the server, so it must not fire per keystroke.
  const runSearch = useCallback(() => setQuery(search.trim()), [search]);

  const clearSearch = useCallback(() => {
    setSearch('');
    setQuery('');
  }, []);

  const visible = content;

  const header = (
    <View>
      <View style={[styles.header, { paddingTop: insets.top + spacing.md }]}>
        <Text style={styles.headerTitle}>Content Hub</Text>
        <Text style={styles.headerSubtitle}>
          Exercise walkthroughs, recovery science, and guided sessions
        </Text>
      </View>

      <View style={styles.searchBar}>
        <Ionicons name="search" size={18} color={colors.text.muted} />
        <TextInput
          style={styles.searchInput}
          value={search}
          onChangeText={setSearch}
          onSubmitEditing={runSearch}
          placeholder="Search any exercise or topic on YouTube"
          placeholderTextColor={colors.text.muted}
          returnKeyType="search"
          accessibilityLabel="Search content"
        />
        {search.length > 0 && (
          <TouchableOpacity onPress={clearSearch} hitSlop={8} accessibilityLabel="Clear search">
            <Ionicons name="close-circle" size={18} color={colors.text.muted} />
          </TouchableOpacity>
        )}
      </View>

      <FlatList
        horizontal
        data={CATEGORIES}
        keyExtractor={(c) => c.label}
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.categoryRow}
        renderItem={({ item: cat }) => {
          const active = !query && category === cat.value;
          return (
            <TouchableOpacity
              style={[
                styles.categoryPill,
                active && { backgroundColor: cat.color + '22', borderColor: cat.color + '66' },
              ]}
              onPress={() => { setCategory(cat.value); clearSearch(); }}
              accessibilityRole="button"
              accessibilityState={{ selected: active }}
            >
              <Ionicons
                name={cat.icon as any}
                size={14}
                color={active ? cat.color : colors.text.muted}
              />
              <Text
                style={[styles.categoryPillText, active && { color: cat.color }]}
                numberOfLines={1}
              >
                {cat.label}
              </Text>
            </TouchableOpacity>
          );
        }}
      />

      {!inlinePlaybackAvailable && (
        <View style={styles.notice}>
          <Ionicons name="open-outline" size={14} color={colors.text.muted} />
          <Text style={styles.noticeText}>Videos open in YouTube</Text>
        </View>
      )}
    </View>
  );

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <FlatList
      style={styles.container}
      data={visible}
      keyExtractor={(item) => item.id}
      ListHeaderComponent={header}
      renderItem={({ item }) => <ContentCard item={item} width={grid.cell} />}
      contentContainerStyle={[styles.listContent, { paddingHorizontal: grid.padding }]}
      ItemSeparatorComponent={() => <View style={{ height: spacing.xl }} />}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />
      }
      ListEmptyComponent={
        <View style={styles.empty}>
          <Ionicons name="search-outline" size={40} color={colors.text.muted} />
          <Text style={styles.emptyTitle}>Nothing here matches that search</Text>
          <TouchableOpacity
            onPress={() =>
              Linking.openURL(
                `https://www.youtube.com/results?search_query=${encodeURIComponent(search)}`
              )
            }
          >
            <Text style={styles.emptyLink}>Search YouTube instead</Text>
          </TouchableOpacity>
        </View>
      }
      showsVerticalScrollIndicator={false}
    />
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  center: { flex: 1, backgroundColor: colors.bg.deep, justifyContent: 'center', alignItems: 'center' },
  listContent: { paddingBottom: 120 },

  header: { paddingBottom: spacing.lg },
  headerTitle: { fontSize: 28, fontWeight: '800', color: colors.text.primary, letterSpacing: -0.5 },
  headerSubtitle: { fontSize: 14, color: colors.text.muted, marginTop: 4, lineHeight: 20 },

  searchBar: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.sm,
    backgroundColor: colors.bg.card, paddingHorizontal: spacing.lg,
    height: 46, borderRadius: radius.lg,
    borderWidth: 1, borderColor: colors.surface.border,
  },
  searchInput: { flex: 1, color: colors.text.primary, fontSize: 15, paddingVertical: 0 },

  categoryRow: { gap: spacing.sm, paddingVertical: spacing.lg },
  categoryPill: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingHorizontal: 14, height: 36, borderRadius: radius.pill,
    backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border,
  },
  categoryPillText: { fontSize: 13, fontWeight: '600', color: colors.text.muted },

  notice: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: spacing.lg },
  noticeText: { fontSize: 12, color: colors.text.muted },

  card: {
    backgroundColor: colors.bg.card, borderRadius: radius.lg,
    borderWidth: 1, borderColor: colors.surface.border, overflow: 'hidden',
  },
  cardBody: { padding: spacing.lg, gap: spacing.xs },
  cardTopRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  typeTag: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    paddingHorizontal: 8, paddingVertical: 4, borderRadius: radius.badge,
  },
  typeTagText: { fontSize: 10, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.4 },
  ratingRow: { flexDirection: 'row', alignItems: 'center', gap: 3 },
  ratingText: { fontSize: 12, fontWeight: '600', color: colors.health.stress },

  cardTitle: { fontSize: 16, fontWeight: '700', color: colors.text.primary, lineHeight: 22, marginTop: 2 },
  channelRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 2 },
  cardDescription: { flex: 1, fontSize: 13, color: colors.text.secondary, lineHeight: 19 },

  cardFooter: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    marginTop: spacing.sm,
  },
  footerItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  footerText: { fontSize: 12, color: colors.text.muted },
  difficultyBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: radius.badge },
  difficultyText: { fontSize: 10, fontWeight: '700', textTransform: 'capitalize' },

  muscleRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, marginTop: spacing.sm },
  muscleTag: {
    maxWidth: '48%',
    backgroundColor: colors.surface.divider,
    paddingHorizontal: 8, paddingVertical: 3, borderRadius: radius.badge,
  },
  muscleText: { fontSize: 10, color: colors.text.secondary, fontWeight: '500' },

  empty: { alignItems: 'center', paddingVertical: spacing['4xl'], gap: spacing.sm },
  emptyTitle: { fontSize: 15, color: colors.text.secondary, textAlign: 'center' },
  emptyLink: { fontSize: 14, color: colors.text.link, fontWeight: '600' },
});
