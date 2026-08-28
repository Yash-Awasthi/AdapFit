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
      <View style={styles.postCard}>
        {/* User Header */}
        <View style={styles.postHeader}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{item.user_name.charAt(0).toUpperCase()}</Text>
          </View>
          <View style={styles.userInfo}>
            <Text style={styles.userName}>{item.user_name}</Text>
            <Text style={styles.timeAgo}>{formatTimeAgo(item.created_at)}</Text>
          </View>
          <Dumbbell size={16} color="#818CF8" />
        </View>

        {/* Workout Content */}
        <View style={styles.workoutContent}>
          <Text style={styles.workoutTitle}>{item.workout_title}</Text>
          <Text style={styles.exercisesSummary}>{item.exercises_summary}</Text>

          {/* Stats Row */}
          <View style={styles.statsRow}>
            <View style={styles.statChip}>
              <Clock size={12} color="#F59E0B" />
              <Text style={styles.statText}>{item.duration_minutes}m</Text>
            </View>
            <View style={styles.statChip}>
              <Flame size={12} color="#EF4444" />
              <Text style={styles.statText}>{(item.total_volume / 1000).toFixed(1)}k kg</Text>
            </View>
          </View>

          {/* Caption */}
          {item.caption ? (
            <Text style={styles.caption}>{item.caption}</Text>
          ) : null}
        </View>

        {/* Action Bar */}
        <View style={styles.actionBar}>
          <TouchableOpacity style={styles.actionBtn} onPress={handleLike}>
            <Animated.View style={{ transform: [{ scale: likeAnim }] }}>
              <Heart
                size={20}
                color={item.is_liked ? '#EF4444' : '#94A3B8'}
                fill={item.is_liked ? '#EF4444' : 'transparent'}
              />
            </Animated.View>
            <Text style={[styles.actionCount, item.is_liked && { color: '#EF4444' }]}>
              {item.likes_count}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionBtn}
            onPress={() => setCommentingPost(commentingPost === item.post_id ? null : item.post_id)}
          >
            <MessageCircle size={20} color="#94A3B8" />
            <Text style={styles.actionCount}>{item.comments_count}</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionBtn}>
            <Share2 size={20} color="#94A3B8" />
          </TouchableOpacity>
        </View>

        {/* Comment Input */}
        {commentingPost === item.post_id && (
          <View style={styles.commentRow}>
            <TextInput
              style={styles.commentInput}
              value={commentText}
              onChangeText={setCommentText}
              placeholder="Add a comment..."
              placeholderTextColor="#475569"
            />
            <TouchableOpacity
              style={styles.sendBtn}
              onPress={() => addComment(item.post_id)}
            >
              <Send size={16} color="#818CF8" />
            </TouchableOpacity>
          </View>
        )}
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyText}>Loading feed...</Text>
      </View>
    );
  }

  if (posts.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <TrendingUp size={40} color="#334155" />
        <Text style={styles.emptyTitle}>No Posts Yet</Text>
        <Text style={styles.emptySubtext}>Complete a workout and share it to see activity here.</Text>
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
  emptyText: { color: '#8B96AB', fontSize: 14 },
  emptyTitle: { fontSize: 18, fontWeight: '600', color: '#F8FAFC', marginTop: 12 },
  emptySubtext: { fontSize: 13, color: '#8B96AB', marginTop: 4, textAlign: 'center' },

  postCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 14,
    marginBottom: 12,
  },
  postHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 10 },
  avatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#4F46E5',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  avatarText: { color: '#fff', fontWeight: '700', fontSize: 14 },
  userInfo: { flex: 1 },
  userName: { fontSize: 14, fontWeight: '600', color: '#F8FAFC' },
  timeAgo: { fontSize: 11, color: '#8B96AB' },

  workoutContent: { marginBottom: 10 },
  workoutTitle: { fontSize: 16, fontWeight: '700', color: '#F8FAFC', marginBottom: 4 },
  exercisesSummary: { fontSize: 13, color: '#CBD5E1', marginBottom: 8 },
  statsRow: { flexDirection: 'row', gap: 8, marginBottom: 8 },
  statChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#0F172A',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  statText: { fontSize: 11, color: '#CBD5E1', fontWeight: '600' },
  caption: { fontSize: 13, color: '#94A3B8', fontStyle: 'italic' },

  actionBar: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: '#334155',
    paddingTop: 10,
    gap: 20,
  },
  actionBtn: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  actionCount: { fontSize: 13, color: '#94A3B8' },

  commentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#334155',
    paddingTop: 10,
  },
  commentInput: {
    flex: 1,
    backgroundColor: '#0F172A',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 13,
    color: '#F8FAFC',
  },
  sendBtn: { padding: 8 },
});
