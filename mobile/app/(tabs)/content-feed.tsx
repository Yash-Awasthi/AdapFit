/**
 * Content Feed — Premium YouTube-like Health Content
 * Glassmorphism cards, gradient thumbnails, category pills, trending section
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Dimensions, RefreshControl, TextInput, ActivityIndicator, Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, radius, glass } from '../../src/theme';
import { GlassCard, SectionHeaderPremium, PillChip } from '../../src/components/PremiumComponents';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const API = 'http://localhost:8000/api/v1';

interface Item {
  id: string; title: string; description: string; content_type: string;
  category: string; difficulty: string; duration_seconds: number;
  rating: number; view_count: number; muscles_targeted: string[];
}

const FALLBACK: Item[] = [
  { id: '1', title: 'Barbell Back Squat — Proper Form', description: 'Learn proper squat form with progressive overload tips', content_type: 'exercise_video', category: 'strength', difficulty: 'all_levels', duration_seconds: 30, rating: 4.7, view_count: 12400, muscles_targeted: ['Quads', 'Glutes', 'Core'] },
  { id: '2', title: '5-Minute Morning Meditation', description: 'Start your day with clarity and mindfulness', content_type: 'meditation', category: 'mental_wellness', difficulty: 'beginner', duration_seconds: 300, rating: 4.8, view_count: 8900, muscles_targeted: [] },
  { id: '3', title: 'Pre-Workout Nutrition Guide', description: 'Optimize your performance with the right fuel', content_type: 'nutrition_tip', category: 'nutrition', difficulty: 'beginner', duration_seconds: 180, rating: 4.5, view_count: 6200, muscles_targeted: [] },
  { id: '4', title: 'Deadlift — Complete Tutorial', description: 'Master the king of all exercises', content_type: 'exercise_video', category: 'strength', difficulty: 'intermediate', duration_seconds: 180, rating: 4.9, view_count: 15600, muscles_targeted: ['Back', 'Glutes', 'Hamstrings'] },
  { id: '5', title: 'Box Breathing for Stress Relief', description: 'Navy SEAL calming technique for instant calm', content_type: 'meditation', category: 'mental_wellness', difficulty: 'beginner', duration_seconds: 300, rating: 4.6, view_count: 7800, muscles_targeted: [] },
  { id: '6', title: 'HRV: Your Recovery Dashboard', description: 'Why heart rate variability matters for recovery', content_type: 'article', category: 'health_knowledge', difficulty: 'intermediate', duration_seconds: 480, rating: 4.8, view_count: 3800, muscles_targeted: [] },
  { id: '7', title: 'Progressive Overload Explained', description: 'The #1 principle for muscle growth', content_type: 'article', category: 'strength', difficulty: 'intermediate', duration_seconds: 240, rating: 4.7, view_count: 9200, muscles_targeted: [] },
  { id: '8', title: 'Sleep Hygiene Masterclass', description: 'Science-backed tips for better sleep quality', content_type: 'sleep_education', category: 'sleep', difficulty: 'beginner', duration_seconds: 600, rating: 4.9, view_count: 11000, muscles_targeted: [] },
];

const CATEGORIES = [
  { label: 'All', icon: 'apps', color: colors.primary },
  { label: 'Strength', icon: 'barbell', color: colors.health.heart },
  { label: 'Cardio', icon: 'walk', color: colors.health.activity },
  { label: 'Mental', icon: 'leaf', color: colors.health.mental },
  { label: 'Nutrition', icon: 'restaurant', color: colors.health.nutrition },
  { label: 'Sleep', icon: 'moon', color: colors.health.sleep },
  { label: 'Knowledge', icon: 'bulb', color: '#F59E0B' },
];

const TYPE_CONFIG: Record<string, { gradient: string[]; emoji: string }> = {
  exercise_video: { gradient: ['#EF4444', '#F97316'], emoji: '🏋️' },
  exercise_gif: { gradient: ['#F97316', '#F59E0B'], emoji: '💪' },
  meditation: { gradient: ['#8B5CF6', '#6366F1'], emoji: '🧘' },
  nutrition_tip: { gradient: ['#22C55E', '#06B6D4'], emoji: '🥗' },
  article: { gradient: ['#3B82F6', '#06B6D4'], emoji: '📖' },
  sleep_education: { gradient: ['#6366F1', '#8B5CF6'], emoji: '😴' },
};

// ===== Content Card =====
const ContentCard: React.FC<{ item: Item; index: number; onPress: () => void }> = ({ item, index, onPress }) => {
  const config = TYPE_CONFIG[item.content_type] || { gradient: ['#64748B', '#475569'], emoji: '📄' };
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(fadeAnim, { toValue: 1, duration: 400, delay: index * 80, useNativeDriver: true }).start();
  }, []);

  return (
    <Animated.View style={{ opacity: fadeAnim }}>
      <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.85}>
        {/* Thumbnail with gradient overlay */}
        <LinearGradient colors={config.gradient as any} style={styles.cardThumbnail}>
          <Text style={styles.cardEmoji}>{config.emoji}</Text>
          {item.duration_seconds > 60 && (
            <View style={styles.durationBadge}>
              <Ionicons name="time" size={10} color="#FFF" />
              <Text style={styles.durationText}>{Math.floor(item.duration_seconds / 60)}:{(item.duration_seconds % 60).toString().padStart(2, '0')}</Text>
            </View>
          )}
          <View style={styles.playOverlay}>
            <Ionicons name="play-circle" size={40} color="rgba(255,255,255,0.9)" />
          </View>
        </LinearGradient>

        {/* Card Body */}
        <View style={styles.cardBody}>
          <View style={styles.cardTopRow}>
            <View style={[styles.typeTag, { backgroundColor: config.gradient[0] + '20' }]}>
              <Text style={[styles.typeTagText, { color: config.gradient[0] }]}>{item.content_type.replace(/_/g, ' ')}</Text>
            </View>
            <View style={styles.ratingRow}>
              <Ionicons name="star" size={12} color="#F59E0B" />
              <Text style={styles.ratingText}>{item.rating}</Text>
            </View>
          </View>

          <Text style={styles.cardTitle} numberOfLines={2}>{item.title}</Text>
          <Text style={styles.cardDescription} numberOfLines={1}>{item.description}</Text>

          <View style={styles.cardFooter}>
            <View style={styles.viewCount}>
              <Ionicons name="eye" size={12} color={colors.text.muted} />
              <Text style={styles.viewCountText}>{(item.view_count / 1000).toFixed(1)}k views</Text>
            </View>
            <View style={[styles.difficultyBadge, {
              backgroundColor: item.difficulty === 'beginner' ? colors.health.calm + '15' : item.difficulty === 'intermediate' ? '#F59E0B15' : colors.health.heart + '15',
            }]}>
              <Text style={[styles.difficultyText, {
                color: item.difficulty === 'beginner' ? colors.health.calm : item.difficulty === 'intermediate' ? '#F59E0B' : colors.health.heart,
              }]}>{item.difficulty}</Text>
            </View>
          </View>

          {item.muscles_targeted?.length > 0 && (
            <View style={styles.muscleRow}>
              {item.muscles_targeted.map((m, i) => (
                <View key={i} style={styles.muscleTag}>
                  <Text style={styles.muscleText}>{m}</Text>
                </View>
              ))}
            </View>
          )}
        </View>
      </TouchableOpacity>
    </Animated.View>
  );
};

// ===== Main Screen =====
export default function ContentFeedScreen() {
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState('All');
  const [content, setContent] = useState<Item[]>([]);
  const [search, setSearch] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const catParam = activeCategory !== 'All' ? `&category=${activeCategory.toLowerCase().replace(' ', '_')}` : '';
      const [feedRes, trendRes] = await Promise.allSettled([
        globalThis.fetch(`${API}/content/feed?page_size=30${catParam}`).then(r => r.json()),
        globalThis.fetch(`${API}/content/trending?limit=5`).then(r => r.json()),
      ]);
      if (feedRes.status === 'fulfilled' && feedRes.value?.items) {
        setContent(feedRes.value.items.map((i: any) => ({
          id: i.id, title: i.title, description: i.description,
          content_type: i.content_type, category: i.category, difficulty: i.difficulty,
          duration_seconds: i.duration_seconds || 0, rating: i.rating || 4.5,
          view_count: i.view_count || 0, muscles_targeted: i.muscles_targeted || [],
        })));
      } else {
        setContent(FALLBACK);
      }
    } catch { setContent(FALLBACK); }
    setLoading(false);
  }, [activeCategory]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  }, [fetchData]);

  const doSearch = async () => {
    if (!search.trim()) { setSearchResults([]); return; }
    try {
      const r = await globalThis.fetch(`${API}/content/search?q=${encodeURIComponent(search)}`);
      const d = await r.json();
      setSearchResults(d.results || []);
    } catch {}
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.contentContainer}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
      showsVerticalScrollIndicator={false}
    >
      {/* Header */}
      <LinearGradient colors={['#6366F1', '#8B5CF6']} style={styles.header}>
        <Text style={styles.headerTitle}>📺 Content Hub</Text>
        <Text style={styles.headerSubtitle}>Health knowledge, exercise guides & wellness content</Text>
      </LinearGradient>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <Ionicons name="search" size={18} color={colors.text.muted} />
          <TextInput
            style={styles.searchInput}
            value={search}
            onChangeText={setSearch}
            placeholder="Search exercises, articles..."
            placeholderTextColor={colors.text.muted}
            onSubmitEditing={doSearch}
            returnKeyType="search"
          />
          {search.length > 0 && (
            <TouchableOpacity onPress={() => { setSearch(''); setSearchResults([]); }}>
              <Ionicons name="close-circle" size={18} color={colors.text.muted} />
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Search Results */}
      {searchResults.length > 0 && (
        <View style={styles.searchResultsContainer}>
          <Text style={styles.searchResultsTitle}>Search Results ({searchResults.length})</Text>
          {searchResults.slice(0, 5).map((r: any, i: number) => (
            <TouchableOpacity key={i} style={styles.searchResultItem}>
              <View style={styles.searchResultIcon}>
                <Ionicons name="document-text" size={16} color={colors.primary} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.searchResultTitle}>{r.title}</Text>
                <Text style={styles.searchResultMeta}>{r.content_type} • {r.difficulty} • ⭐{r.rating}</Text>
              </View>
              <Ionicons name="chevron-forward" size={16} color={colors.text.muted} />
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Category Pills */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.categoriesScroll}>
        <View style={styles.categoriesRow}>
          {CATEGORIES.map((cat) => (
            <TouchableOpacity
              key={cat.label}
              style={[styles.categoryPill, activeCategory === cat.label && { backgroundColor: cat.color + '20', borderColor: cat.color + '50' }]}
              onPress={() => setActiveCategory(cat.label)}
              activeOpacity={0.7}
            >
              <Ionicons name={cat.icon as any} size={14} color={activeCategory === cat.label ? cat.color : colors.text.muted} />
              <Text style={[styles.categoryPillText, activeCategory === cat.label && { color: cat.color }]}>{cat.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>

      {/* Content Grid */}
      {loading ? (
        <ActivityIndicator size="large" color={colors.primary} style={{ marginTop: 40 }} />
      ) : (
        <View style={styles.contentGrid}>
          {content.map((item, index) => (
            <ContentCard key={item.id} item={item} index={index} onPress={() => {}} />
          ))}
        </View>
      )}

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  contentContainer: { paddingBottom: 100 },

  // Header
  header: { paddingTop: 56, paddingBottom: spacing.xl, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 28, borderBottomRightRadius: 28 },
  headerTitle: { fontSize: 24, fontWeight: '800', color: '#FFF' },
  headerSubtitle: { fontSize: 14, color: 'rgba(255,255,255,0.7)', marginTop: 4 },

  // Search
  searchContainer: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.lg },
  searchBar: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.sm,
    backgroundColor: colors.bg.card, paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md, borderRadius: radius.lg,
    borderWidth: 1, borderColor: colors.surface.border,
  },
  searchInput: { flex: 1, color: colors.text.primary, fontSize: 15 },

  // Search Results
  searchResultsContainer: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.md },
  searchResultsTitle: { fontSize: 14, fontWeight: '700', color: colors.text.primary, marginBottom: spacing.sm },
  searchResultItem: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.md,
    backgroundColor: colors.bg.card, padding: spacing.md, borderRadius: radius.md,
    marginBottom: spacing.xs, borderWidth: 1, borderColor: colors.surface.border,
  },
  searchResultIcon: { width: 32, height: 32, borderRadius: 8, backgroundColor: colors.primaryMuted, justifyContent: 'center', alignItems: 'center' },
  searchResultTitle: { fontSize: 13, fontWeight: '600', color: colors.text.primary },
  searchResultMeta: { fontSize: 11, color: colors.text.muted, marginTop: 2 },

  // Categories
  categoriesScroll: { marginTop: spacing.lg },
  categoriesRow: { flexDirection: 'row', paddingHorizontal: spacing.screenPadding, gap: spacing.sm },
  categoryPill: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingHorizontal: 14, paddingVertical: 8, borderRadius: 999,
    backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border,
  },
  categoryPillText: { fontSize: 13, fontWeight: '600', color: colors.text.muted },

  // Content Grid
  contentGrid: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.lg },

  // Content Card
  card: {
    backgroundColor: colors.bg.card, borderRadius: radius.lg,
    marginBottom: spacing.lg, borderWidth: 1, borderColor: colors.surface.border,
    overflow: 'hidden',
  },
  cardThumbnail: {
    height: 140, justifyContent: 'center', alignItems: 'center',
  },
  cardEmoji: { fontSize: 48 },
  playOverlay: {
    position: 'absolute', justifyContent: 'center', alignItems: 'center',
    width: '100%', height: '100%',
  },
  durationBadge: {
    position: 'absolute', bottom: spacing.sm, right: spacing.sm,
    flexDirection: 'row', alignItems: 'center', gap: 4,
    backgroundColor: '#000000AA', paddingHorizontal: spacing.sm,
    paddingVertical: 3, borderRadius: radius.xs,
  },
  durationText: { fontSize: 11, color: '#FFF', fontWeight: '600' },
  cardBody: { padding: spacing.lg },
  cardTopRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.sm },
  typeTag: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  typeTagText: { fontSize: 10, fontWeight: '700', textTransform: 'uppercase' },
  ratingRow: { flexDirection: 'row', alignItems: 'center', gap: 3 },
  ratingText: { fontSize: 12, fontWeight: '600', color: '#F59E0B' },
  cardTitle: { fontSize: 16, fontWeight: '700', color: colors.text.primary, lineHeight: 22 },
  cardDescription: { fontSize: 13, color: colors.text.muted, marginTop: 4 },
  cardFooter: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: spacing.md },
  viewCount: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  viewCountText: { fontSize: 12, color: colors.text.muted },
  difficultyBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  difficultyText: { fontSize: 10, fontWeight: '600', textTransform: 'capitalize' },
  muscleRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, marginTop: spacing.md },
  muscleTag: { backgroundColor: colors.surface.divider, paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  muscleText: { fontSize: 10, color: colors.text.secondary, fontWeight: '500' },
});
