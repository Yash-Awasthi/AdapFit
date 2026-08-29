/**
 * Forums — Premium Community Forums
 * Glassmorphism cards, staggered post feed, reactions
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Dimensions, Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../../src/theme';
import { ScreenWrapper } from '../../src/components/ScreenWrapper';
import { GlassCard, SectionHeaderPremium, PillChip } from '../../src/components/PremiumComponents';
import { StaggeredList } from '../../src/components/AnimationSystem';

const CATEGORIES = ['All', 'Fitness', 'Nutrition', 'Mental Health', 'Sleep', 'General'];

const POSTS = [
  { id: 1, title: 'Best recovery routine after heavy leg day?', author: 'Mike R.', avatar: '👨', category: 'Fitness', replies: 24, likes: 56, time: '2h ago', hot: true },
  { id: 2, title: 'How I fixed my sleep schedule in 2 weeks', author: 'Sarah M.', avatar: '👩', category: 'Sleep', replies: 18, likes: 89, time: '4h ago', hot: true },
  { id: 3, title: 'Simple high-protein meal prep ideas', author: 'Emma L.', avatar: '👩', category: 'Nutrition', replies: 32, likes: 120, time: '6h ago', hot: false },
  { id: 4, title: 'Managing work stress with breathing exercises', author: 'James K.', avatar: '🧑', category: 'Mental Health', replies: 15, likes: 45, time: '8h ago', hot: false },
  { id: 5, title: 'My 30-day meditation journey results', author: 'Lisa P.', avatar: '👩', category: 'Mental Health', replies: 28, likes: 95, time: '12h ago', hot: true },
  { id: 6, title: 'What supplements actually work?', author: 'Tom H.', avatar: '🧑', category: 'General', replies: 42, likes: 78, time: '1d ago', hot: false },
];

export default function ForumsScreen() {
  const [selectedCategory, setSelectedCategory] = useState('All');

  return (
    <ScreenWrapper
      title="Forums"
      subtitle="Community discussions"
      gradient={['#8B5CF6', '#6366F1']}
      rightAction={{ icon: 'create', onPress: () => {} }}
    >
      {/* Category Filter */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterScroll}>
        <View style={styles.filterRow}>
          {CATEGORIES.map(c => (
            <PillChip key={c} label={c} active={selectedCategory === c} onPress={() => setSelectedCategory(c)} />
          ))}
        </View>
      </ScrollView>

      {/* Posts */}
      <StaggeredList staggerDelay={80} animationType="slideIn">
        {POSTS.filter(p => selectedCategory === 'All' || p.category === selectedCategory).map(post => (
          <GlassCard key={post.id} variant="light" style={styles.postCard}>
            <View style={styles.postHeader}>
              <Text style={styles.postAvatar}>{post.avatar}</Text>
              <View style={{ flex: 1 }}>
                <Text style={styles.postAuthor}>{post.author}</Text>
                <Text style={styles.postTime}>{post.time}</Text>
              </View>
              {post.hot && (
                <View style={styles.hotBadge}>
                  <Ionicons name="flame" size={12} color="#F97316" />
                  <Text style={styles.hotText}>Hot</Text>
                </View>
              )}
            </View>
            <Text style={styles.postTitle}>{post.title}</Text>
            <View style={styles.postMeta}>
              <View style={[styles.categoryBadge, { backgroundColor: colors.primary + '15' }]}>
                <Text style={[styles.categoryText, { color: colors.primary }]}>{post.category}</Text>
              </View>
              <View style={styles.postStats}>
                <View style={styles.postStat}>
                  <Ionicons name="chatbubble" size={12} color={colors.text.muted} />
                  <Text style={styles.postStatText}>{post.replies}</Text>
                </View>
                <View style={styles.postStat}>
                  <Ionicons name="heart" size={12} color={colors.health.heart} />
                  <Text style={styles.postStatText}>{post.likes}</Text>
                </View>
              </View>
            </View>
          </GlassCard>
        ))}
      </StaggeredList>
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  filterScroll: { marginBottom: spacing.lg },
  filterRow: { flexDirection: 'row', paddingHorizontal: spacing.screenPadding, gap: spacing.sm },

  postCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.md },
  postHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, marginBottom: spacing.sm },
  postAvatar: { fontSize: 28 },
  postAuthor: { fontSize: 14, fontWeight: '700', color: colors.text.primary },
  postTime: { fontSize: 11, color: colors.text.muted, marginTop: 1 },
  hotBadge: { flexDirection: 'row', alignItems: 'center', gap: 3, paddingHorizontal: 8, paddingVertical: 3, backgroundColor: '#F9731615', borderRadius: 6 },
  hotText: { fontSize: 11, fontWeight: '700', color: '#F97316' },

  postTitle: { fontSize: 15, fontWeight: '700', color: colors.text.primary, lineHeight: 21, marginBottom: spacing.sm },

  postMeta: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  categoryBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  categoryText: { fontSize: 11, fontWeight: '600' },
  postStats: { flexDirection: 'row', gap: spacing.md },
  postStat: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  postStatText: { fontSize: 12, color: colors.text.muted },
});
