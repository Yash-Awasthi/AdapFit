/**
 * Forums — community discussion threads.
 *
 * Backed by the same community feed as Social: Social shows challenges and
 * shared workouts, Forums shows the discussion posts within that feed.
 */
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet, TextInput,
  ActivityIndicator, RefreshControl, KeyboardAvoidingView, Platform, Modal,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { colors, spacing, radius } from '../../src/theme';
import { useTabBarHeight } from '../../src/theme/layout';
import { getJson, postJson, asArray } from '../../src/services/http';
import { useUserStore } from '../../src/stores';

const CATEGORIES = ['all', 'fitness', 'nutrition', 'mental health', 'sleep', 'general'];

interface Post {
  id: string;
  user_name: string;
  title: string;
  caption: string;
  category: string;
  likes: number;
  comments_count: number;
  shared_at: string;
}

interface Comment {
  id: string;
  user_name: string;
  text: string;
  created_at: string;
}

function relativeTime(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function Avatar({ name }: { name: string }) {
  return (
    <View style={styles.avatar}>
      <Text style={styles.avatarText}>{(name || '?').charAt(0).toUpperCase()}</Text>
    </View>
  );
}

function ThreadModal({ post, userId, onClose, onChanged }: {
  post: Post; userId: string; onClose: () => void; onChanged: () => void;
}) {
  const insets = useSafeAreaInsets();
  const [comments, setComments] = useState<Comment[]>([]);
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(true);
  const [posting, setPosting] = useState(false);

  const load = useCallback(async () => {
    const data = await getJson<Comment[]>(`/community/${post.id}/comments`);
    setComments(asArray<Comment>(data));
    setLoading(false);
  }, [post.id]);

  useEffect(() => { load(); }, [load]);

  const submit = async () => {
    const body = text.trim();
    if (!body || posting) return;
    setPosting(true);
    const created = await postJson<Comment>(`/community/${post.id}/comments?user_id=${userId}`, { text: body });
    if (created) {
      setText('');
      await load();
      onChanged();
    }
    setPosting(false);
  };

  return (
    <Modal visible animationType="slide" onRequestClose={onClose}>
      <KeyboardAvoidingView
        style={styles.modal}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <View style={[styles.modalHeader, { paddingTop: insets.top + spacing.sm }]}>
          <TouchableOpacity onPress={onClose} hitSlop={12} accessibilityLabel="Close thread">
            <Ionicons name="chevron-down" size={24} color={colors.text.primary} />
          </TouchableOpacity>
          <Text style={styles.modalTitle} numberOfLines={1}>Thread</Text>
          <View style={{ width: 24 }} />
        </View>

        <FlatList
          data={comments}
          keyExtractor={(c) => c.id}
          contentContainerStyle={styles.modalList}
          ListHeaderComponent={
            <View style={styles.threadHead}>
              <View style={styles.postTop}>
                <Avatar name={post.user_name} />
                <View style={{ flex: 1 }}>
                  <Text style={styles.postAuthor}>{post.user_name}</Text>
                  <Text style={styles.postMeta}>{relativeTime(post.shared_at)}</Text>
                </View>
              </View>
              <Text style={styles.threadTitle}>{post.title}</Text>
              {!!post.caption && <Text style={styles.threadBody}>{post.caption}</Text>}
              <Text style={styles.threadCount}>
                {comments.length === 0 ? 'No replies yet' : `${comments.length} ${comments.length === 1 ? 'reply' : 'replies'}`}
              </Text>
            </View>
          }
          renderItem={({ item }) => (
            <View style={styles.comment}>
              <Avatar name={item.user_name} />
              <View style={{ flex: 1 }}>
                <View style={styles.commentTop}>
                  <Text style={styles.postAuthor}>{item.user_name}</Text>
                  <Text style={styles.postMeta}>{relativeTime(item.created_at)}</Text>
                </View>
                <Text style={styles.commentText}>{item.text}</Text>
              </View>
            </View>
          )}
          ListEmptyComponent={
            loading ? <ActivityIndicator color={colors.primary} style={{ marginTop: spacing.xl }} /> : null
          }
        />

        <View style={[styles.replyBar, { paddingBottom: insets.bottom + spacing.sm }]}>
          <TextInput
            style={styles.replyInput}
            value={text}
            onChangeText={setText}
            placeholder="Write a reply"
            placeholderTextColor={colors.text.muted}
            multiline
            maxLength={500}
            accessibilityLabel="Reply text"
          />
          <TouchableOpacity
            style={[styles.replySend, (!text.trim() || posting) && styles.disabled]}
            onPress={submit}
            disabled={!text.trim() || posting}
            accessibilityLabel="Post reply"
          >
            {posting
              ? <ActivityIndicator size="small" color="#FFF" />
              : <Ionicons name="arrow-up" size={18} color="#FFF" />}
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

function ComposeModal({ userId, onClose, onCreated }: {
  userId: string; onClose: () => void; onCreated: () => void;
}) {
  const insets = useSafeAreaInsets();
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [category, setCategory] = useState('general');
  const [posting, setPosting] = useState(false);

  const submit = async () => {
    if (!title.trim() || posting) return;
    setPosting(true);
    const created = await postJson(`/community/share?user_id=${userId}`, {
      title: title.trim(), caption: body.trim(), category, is_public: true,
    });
    setPosting(false);
    if (created) {
      onCreated();
      onClose();
    }
  };

  return (
    <Modal visible animationType="slide" onRequestClose={onClose}>
      <KeyboardAvoidingView style={styles.modal} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <View style={[styles.modalHeader, { paddingTop: insets.top + spacing.sm }]}>
          <TouchableOpacity onPress={onClose} hitSlop={12} accessibilityLabel="Cancel">
            <Ionicons name="close" size={24} color={colors.text.primary} />
          </TouchableOpacity>
          <Text style={styles.modalTitle}>New post</Text>
          <TouchableOpacity onPress={submit} disabled={!title.trim() || posting} hitSlop={12}>
            <Text style={[styles.postAction, (!title.trim() || posting) && { color: colors.text.muted }]}>
              Post
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.composeBody}>
          <TextInput
            style={styles.composeTitle}
            value={title}
            onChangeText={setTitle}
            placeholder="Ask a question or share something"
            placeholderTextColor={colors.text.muted}
            maxLength={200}
            accessibilityLabel="Post title"
          />
          <TextInput
            style={styles.composeText}
            value={body}
            onChangeText={setBody}
            placeholder="Add detail (optional)"
            placeholderTextColor={colors.text.muted}
            multiline
            maxLength={1000}
            accessibilityLabel="Post detail"
          />
          <View style={styles.chipRow}>
            {CATEGORIES.filter((c) => c !== 'all').map((c) => (
              <TouchableOpacity
                key={c}
                style={[styles.chip, category === c && styles.chipActive]}
                onPress={() => setCategory(c)}
              >
                <Text style={[styles.chipText, category === c && styles.chipTextActive]}>{c}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

export default function ForumsScreen() {
  const insets = useSafeAreaInsets();
  const tabBarHeight = useTabBarHeight();
  const userId = useUserStore((s) => s.userId);
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [category, setCategory] = useState('all');
  const [openPost, setOpenPost] = useState<Post | null>(null);
  const [composing, setComposing] = useState(false);
  const [liked, setLiked] = useState<Record<string, boolean>>({});

  const load = useCallback(async () => {
    const data = await getJson<Post[]>(`/community/feed?user_id=${userId}&limit=50`);
    setPosts(asArray<Post>(data));
    setLoading(false);
  }, [userId]);

  useEffect(() => { load(); }, [load]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }, [load]);

  const toggleLike = async (post: Post) => {
    Haptics.selectionAsync();
    const result = await postJson<{ liked: boolean; total_likes: number }>(
      `/community/${post.id}/like?user_id=${userId}`
    );
    if (!result) return;
    setLiked((prev) => ({ ...prev, [post.id]: result.liked }));
    setPosts((prev) =>
      prev.map((p) => (p.id === post.id ? { ...p, likes: result.total_likes } : p))
    );
  };

  const visible = useMemo(
    () => (category === 'all' ? posts : posts.filter((p) => p.category === category)),
    [posts, category]
  );

  return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insets.top + spacing.xl }]}>
        <View style={{ flex: 1 }}>
          <Text style={styles.headerTitle}>Forums</Text>
          <Text style={styles.headerSubtitle}>Ask, answer, and compare notes</Text>
        </View>
        <TouchableOpacity
          style={styles.newButton}
          onPress={() => setComposing(true)}
          accessibilityLabel="New post"
        >
          <Ionicons name="create-outline" size={20} color="#FFF" />
        </TouchableOpacity>
      </View>

      <FlatList
        horizontal
        data={CATEGORIES}
        keyExtractor={(c) => c}
        showsHorizontalScrollIndicator={false}
        style={styles.chipScroll}
        contentContainerStyle={styles.chipRowScroll}
        renderItem={({ item: c }) => (
          <TouchableOpacity
            style={[styles.chip, category === c && styles.chipActive]}
            onPress={() => setCategory(c)}
            accessibilityState={{ selected: category === c }}
          >
            <Text style={[styles.chipText, category === c && styles.chipTextActive]}>{c}</Text>
          </TouchableOpacity>
        )}
      />

      {loading ? (
        <ActivityIndicator size="large" color={colors.primary} style={{ marginTop: spacing['4xl'] }} />
      ) : (
        <FlatList
          data={visible}
          keyExtractor={(p) => p.id}
          contentContainerStyle={[styles.list, { paddingBottom: tabBarHeight + spacing.xl }]}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />
          }
          ItemSeparatorComponent={() => <View style={{ height: spacing.md }} />}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={styles.post}
              activeOpacity={0.85}
              onPress={() => setOpenPost(item)}
              accessibilityRole="button"
              accessibilityLabel={`Open thread: ${item.title}`}
            >
              <View style={styles.postTop}>
                <Avatar name={item.user_name} />
                <View style={{ flex: 1 }}>
                  <Text style={styles.postAuthor}>{item.user_name}</Text>
                  <Text style={styles.postMeta}>
                    {relativeTime(item.shared_at)} · {item.category}
                  </Text>
                </View>
              </View>

              <Text style={styles.postTitle} numberOfLines={2}>{item.title}</Text>
              {!!item.caption && (
                <Text style={styles.postCaption} numberOfLines={2}>{item.caption}</Text>
              )}

              <View style={styles.postActions}>
                <TouchableOpacity
                  style={styles.postAction2}
                  onPress={() => toggleLike(item)}
                  accessibilityLabel={liked[item.id] ? 'Unlike' : 'Like'}
                >
                  <Ionicons
                    name={liked[item.id] ? 'heart' : 'heart-outline'}
                    size={16}
                    color={liked[item.id] ? colors.health.heart : colors.text.muted}
                  />
                  <Text style={styles.postActionText}>{item.likes}</Text>
                </TouchableOpacity>
                <View style={styles.postAction2}>
                  <Ionicons name="chatbubble-outline" size={15} color={colors.text.muted} />
                  <Text style={styles.postActionText}>{item.comments_count}</Text>
                </View>
                <View style={{ flex: 1 }} />
                <Text style={styles.openHint}>Open</Text>
                <Ionicons name="chevron-forward" size={14} color={colors.text.muted} />
              </View>
            </TouchableOpacity>
          )}
          ListEmptyComponent={
            <View style={styles.empty}>
              <Ionicons name="chatbubbles-outline" size={40} color={colors.text.muted} />
              <Text style={styles.emptyTitle}>No discussions yet</Text>
              <Text style={styles.emptyText}>Start the first thread and others can reply to it.</Text>
              <TouchableOpacity style={styles.emptyButton} onPress={() => setComposing(true)}>
                <Ionicons name="create-outline" size={16} color="#FFF" />
                <Text style={styles.emptyButtonText}>Write a post</Text>
              </TouchableOpacity>
            </View>
          }
        />
      )}

      {openPost && (
        <ThreadModal
          post={openPost}
          userId={userId}
          onClose={() => setOpenPost(null)}
          onChanged={load}
        />
      )}
      {composing && (
        <ComposeModal userId={userId} onClose={() => setComposing(false)} onCreated={load} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },

  header: {
    flexDirection: 'row', alignItems: 'flex-end', gap: spacing.md,
    paddingHorizontal: spacing.screenPadding, paddingBottom: spacing.lg,
  },
  headerTitle: { fontSize: 28, fontWeight: '800', color: colors.text.primary, letterSpacing: -0.5 },
  headerSubtitle: { fontSize: 14, color: colors.text.muted, marginTop: 4 },
  newButton: {
    width: 44, height: 44, borderRadius: 22, backgroundColor: colors.primary,
    alignItems: 'center', justifyContent: 'center',
  },

  chipScroll: { flexGrow: 0 },
  chipRowScroll: { gap: spacing.sm, paddingHorizontal: spacing.screenPadding, paddingBottom: spacing.lg },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginTop: spacing.lg },
  chip: {
    paddingHorizontal: 14, height: 34, justifyContent: 'center',
    borderRadius: radius.pill, backgroundColor: colors.bg.card,
    borderWidth: 1, borderColor: colors.surface.border,
  },
  chipActive: { backgroundColor: colors.primary + '22', borderColor: colors.primary + '66' },
  chipText: { fontSize: 13, fontWeight: '600', color: colors.text.muted, textTransform: 'capitalize' },
  chipTextActive: { color: colors.primaryLight },

  list: { paddingHorizontal: spacing.screenPadding },
  post: {
    backgroundColor: colors.bg.card, borderRadius: radius.lg,
    borderWidth: 1, borderColor: colors.surface.border, padding: spacing.lg,
  },
  postTop: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginBottom: spacing.sm },
  avatar: {
    width: 32, height: 32, borderRadius: 16, backgroundColor: colors.primaryMuted,
    alignItems: 'center', justifyContent: 'center',
  },
  avatarText: { fontSize: 14, fontWeight: '700', color: colors.primaryLight },
  postAuthor: { fontSize: 13, fontWeight: '700', color: colors.text.primary },
  postMeta: { fontSize: 11, color: colors.text.muted, marginTop: 1, textTransform: 'capitalize' },
  postTitle: { fontSize: 16, fontWeight: '700', color: colors.text.primary, lineHeight: 22 },
  postCaption: { fontSize: 13, color: colors.text.secondary, lineHeight: 19, marginTop: 4 },
  postActions: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.lg,
    marginTop: spacing.md, paddingTop: spacing.sm,
    borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.surface.border,
  },
  postAction2: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  postActionText: { fontSize: 12, color: colors.text.muted, fontWeight: '600' },
  openHint: { fontSize: 12, color: colors.text.muted, marginRight: 2 },

  empty: { alignItems: 'center', paddingVertical: spacing['4xl'], gap: spacing.sm },
  emptyTitle: { fontSize: 16, fontWeight: '700', color: colors.text.primary },
  emptyText: { fontSize: 13, color: colors.text.muted, textAlign: 'center', paddingHorizontal: spacing.xl },
  emptyButton: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.sm,
    backgroundColor: colors.primary, paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md, borderRadius: radius.button, marginTop: spacing.md,
  },
  emptyButtonText: { fontSize: 14, fontWeight: '700', color: '#FFF' },

  modal: { flex: 1, backgroundColor: colors.bg.deep },
  modalHeader: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: spacing.lg, paddingBottom: spacing.md,
    borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.surface.border,
  },
  modalTitle: { fontSize: 16, fontWeight: '700', color: colors.text.primary },
  postAction: { fontSize: 15, fontWeight: '700', color: colors.primaryLight },
  modalList: { padding: spacing.lg, paddingBottom: spacing['4xl'] },

  threadHead: { marginBottom: spacing.lg },
  threadTitle: { fontSize: 18, fontWeight: '700', color: colors.text.primary, lineHeight: 25 },
  threadBody: { fontSize: 14, color: colors.text.secondary, lineHeight: 21, marginTop: spacing.sm },
  threadCount: {
    fontSize: 12, color: colors.text.muted, marginTop: spacing.lg,
    paddingTop: spacing.md,
    borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.surface.border,
  },

  comment: { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.lg },
  commentTop: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  commentText: { fontSize: 14, color: colors.text.secondary, lineHeight: 20, marginTop: 3 },

  replyBar: {
    flexDirection: 'row', alignItems: 'flex-end', gap: spacing.sm,
    padding: spacing.md,
    borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.surface.border,
  },
  replyInput: {
    flex: 1, maxHeight: 110, backgroundColor: colors.bg.card,
    borderRadius: radius.lg, paddingHorizontal: spacing.lg, paddingVertical: spacing.md,
    fontSize: 14, color: colors.text.primary,
    borderWidth: 1, borderColor: colors.surface.border,
  },
  replySend: {
    width: 40, height: 40, borderRadius: 20, backgroundColor: colors.primary,
    alignItems: 'center', justifyContent: 'center',
  },
  disabled: { backgroundColor: colors.bg.elevated },

  composeBody: { padding: spacing.lg, gap: spacing.md },
  composeTitle: {
    fontSize: 18, fontWeight: '700', color: colors.text.primary,
    backgroundColor: colors.bg.card, borderRadius: radius.lg, padding: spacing.lg,
    borderWidth: 1, borderColor: colors.surface.border,
  },
  composeText: {
    minHeight: 140, textAlignVertical: 'top',
    fontSize: 14, color: colors.text.primary, lineHeight: 21,
    backgroundColor: colors.bg.card, borderRadius: radius.lg, padding: spacing.lg,
    borderWidth: 1, borderColor: colors.surface.border,
  },
});
