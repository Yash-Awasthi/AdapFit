/**
 * TikTok-style vertical activity feed showing recent workouts.
 * Supports like, comment, share actions with animated interactions.
 */

import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  TextInput,
  StyleSheet,
  Animated,
  Easing,
  Dimensions,
} from 'react-native';
import {
  Heart, MessageCircle, Share2, Dumbbell, Clock, Flame,
  TrendingUp, Send,
} from 'lucide-react-native';
import * as Haptics from 'expo-haptics';
import { API_BASE_URL } from '../services/config';
import { useUserStore } from '../stores';
import { useTheme } from '../services/theme';

const API = API_BASE_URL;
const SCREEN_WIDTH = Dimensions.get('window').width;

interface FeedPost {
  post_id: string;
  user_id: string;
  user_name: string;
  workout_title: string;
  exercises_summary: string;
  duration_minutes: number;
  total_volume: number;
  caption: string;
  likes_count: number;
  comments_count: number;
  is_liked: boolean;
  created_at: string;
}

interface ActivityFeedProps {
  userId?: string;
}

export function ActivityFeed({ userId = 'default' }: ActivityFeedProps) {
  const { theme } = useTheme();
  const [posts, setPosts] = useState<FeedPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [commentingPost, setCommentingPost] = useState<string | null>(null);
  const [commentText, setCommentText] = useState('');

  React.useEffect(() => { fetchFeed(); }, []);

  async function fetchFeed() {
    try {
      const res = await fetch(`${API}/api/v1/activity-feed?user_id=${userId}&limit=20`);
      if (res.ok) {
        const data = await res.json();
        setPosts(data.items || []);
      }
    } catch {}
    setLoading(false);
  }

  async function toggleLike(post: FeedPost) {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    try {
      const res = await fetch(
        `${API}/api/v1/activity-feed/${post.post_id}/like?user_id=${userId}`,
        { method: 'POST' }
      );
      if (res.ok) {
        const data = await res.json();
        setPosts((prev) =>
          prev.map((p) =>
            p.post_id === post.post_id
              ? { ...p, is_liked: data.liked, likes_count: data.likes_count }
              : p
          )
        );
      }
    } catch {}
  }

  async function addComment(postId: string) {
    if (!commentText.trim()) return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    try {
      const res = await fetch(`${API}/api/v1/activity-feed/${postId}/comment?user_id=${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, content: commentText }),
      });
      if (res.ok) {
        setPosts((prev) =>
          prev.map((p) =>
            p.post_id === postId
              ? { ...p, comments_count: p.comments_count + 1 }
              : p
          )
        );
        setCommentText('');
        setCommentingPost(null);
      }
    } catch {}
  }

  function formatTimeAgo(dateStr: string) {
    try {
      const diff = Date.now() - new Date(dateStr).getTime();
      const minutes = Math.floor(diff / 60000);
      if (minutes < 1) return 'just now';
      if (minutes < 60) return `${minutes}m ago`;
      const hours = Math.floor(minutes / 60);
      if (hours < 24) return `${hours}h ago`;
      const days = Math.floor(hours / 24);
      return `${days}d ago`;
    } catch {
      return '';
    }
  }

  const renderPost = ({ item }: { item: FeedPost }) => {
    const likeAnim = useRef(new Animated.Value(1)).current;

    function handleLike() {
      Animated.sequence([
        Animated.timing(likeAnim, { toValue: 1.3, duration: 150, useNativeDriver: true }),
        Animated.timing(likeAnim, { toValue: 1, duration: 150, useNativeDriver: true }),
      ]).start();
      toggleLike(item);
    }

    return (
      <View style={[styles.postCard, { backgroundColor: theme.surface }]}>
        {/* User Header */}
        <View style={styles.postHeader}>
          <View style={[styles.avatar, { backgroundColor: theme.primary }]}>
            <Text style={styles.avatarText}>{item.user_name.charAt(0).toUpperCase()}</Text>
          </View>
          <View style={styles.userInfo}>
            <Text style={[styles.userName, { color: theme.text }]}>{item.user_name}</Text>
            <Text style={[styles.timeAgo, { color: theme.textMuted }]}>{formatTimeAgo(item.created_at)}</Text>
          </View>
          <Dumbbell size={16} color={theme.primaryLight} />
        </View>

        {/* Workout Content */}
        <View style={styles.workoutContent}>
          <Text style={[styles.workoutTitle, { color: theme.text }]}>{item.workout_title}</Text>
          <Text style={[styles.exercisesSummary, { color: theme.textSecondary }]}>{item.exercises_summary}</Text>

          {/* Stats Row */}
          <View style={styles.statsRow}>
            <View style={[styles.statChip, { backgroundColor: theme.background }]}>
              <Clock size={12} color={theme.orange} />
              <Text style={[styles.statText, { color: theme.textSecondary }]}>{item.duration_minutes}m</Text>
            </View>
            <View style={[styles.statChip, { backgroundColor: theme.background }]}>
              <Flame size={12} color={theme.danger} />
              <Text style={[styles.statText, { color: theme.textSecondary }]}>{(item.total_volume / 1000).toFixed(1)}k kg</Text>
            </View>
          </View>

          {/* Caption */}
          {item.caption ? (
            <Text style={[styles.caption, { color: theme.textSecondary }]}>{item.caption}</Text>
          ) : null}
        </View>

        {/* Action Bar */}
        <View style={[styles.actionBar, { borderTopColor: theme.border }]}>
          <TouchableOpacity style={styles.actionBtn} onPress={handleLike}>
            <Animated.View style={{ transform: [{ scale: likeAnim }] }}>
              <Heart
                size={20}
                color={item.is_liked ? theme.danger : theme.textSecondary}
                fill={item.is_liked ? theme.danger : 'transparent'}
              />
            </Animated.View>
            <Text style={[styles.actionCount, { color: item.is_liked ? theme.danger : theme.textSecondary }]}>
              {item.likes_count}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionBtn}
            onPress={() => setCommentingPost(commentingPost === item.post_id ? null : item.post_id)}
          >
            <MessageCircle size={20} color={theme.textSecondary} />
            <Text style={[styles.actionCount, { color: theme.textSecondary }]}>{item.comments_count}</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionBtn}>
            <Share2 size={20} color={theme.textSecondary} />
          </TouchableOpacity>
        </View>

        {/* Comment Input */}
        {commentingPost === item.post_id && (
          <View style={[styles.commentRow, { borderTopColor: theme.border }]}>
            <TextInput
              style={[styles.commentInput, { backgroundColor: theme.background, color: theme.text }]}
              value={commentText}
              onChangeText={setCommentText}
              placeholder="Add a comment..."
              placeholderTextColor={theme.textMuted}
            />
            <TouchableOpacity
              style={styles.sendBtn}
              onPress={() => addComment(item.post_id)}
            >
              <Send size={16} color={theme.primaryLight} />
            </TouchableOpacity>
          </View>
        )}
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={[styles.emptyText, { color: theme.textMuted }]}>Loading feed...</Text>
      </View>
    );
  }

  if (posts.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <TrendingUp size={40} color={theme.border} />
        <Text style={[styles.emptyTitle, { color: theme.text }]}>No Posts Yet</Text>
        <Text style={[styles.emptySubtext, { color: theme.textMuted }]}>Complete a workout and share it to see activity here.</Text>
      </View>
    );
  }

  return (
    <FlatList
      data={posts}
      keyExtractor={(item) => item.post_id}
      renderItem={renderPost}
      contentContainerStyle={styles.list}
      showsVerticalScrollIndicator={false}
    />
  );
}

const styles = StyleSheet.create({
  list: { padding: 12 },
  emptyContainer: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 40 },
  emptyText: { fontSize: 14 },
  emptyTitle: { fontSize: 18, fontWeight: '600', marginTop: 12 },
  emptySubtext: { fontSize: 13, marginTop: 4, textAlign: 'center' },

  postCard: {
    borderRadius: 16,
    padding: 14,
    marginBottom: 12,
  },
  postHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 10 },
  avatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  avatarText: { color: '#fff', fontWeight: '700', fontSize: 14 },
  userInfo: { flex: 1 },
  userName: { fontSize: 14, fontWeight: '600' },
  timeAgo: { fontSize: 11 },

  workoutContent: { marginBottom: 10 },
  workoutTitle: { fontSize: 16, fontWeight: '700', marginBottom: 4 },
  exercisesSummary: { fontSize: 13, marginBottom: 8 },
  statsRow: { flexDirection: 'row', gap: 8, marginBottom: 8 },
  statChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  statText: { fontSize: 11, fontWeight: '600' },
  caption: { fontSize: 13, fontStyle: 'italic' },

  actionBar: {
    flexDirection: 'row',
    borderTopWidth: 1,
    paddingTop: 10,
    gap: 20,
  },
  actionBtn: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  actionCount: { fontSize: 13 },

  commentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 10,
    borderTopWidth: 1,
    paddingTop: 10,
  },
  commentInput: {
    flex: 1,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 13,
  },
  sendBtn: { padding: 8 },
});
