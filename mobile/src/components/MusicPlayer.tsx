import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Play, Pause, SkipForward, SkipBack, Music } from 'lucide-react-native';
import * as Haptics from 'expo-haptics';
import { API_BASE_URL } from '../services/config';
import { useUserStore } from '../stores';
import { useTheme } from '../services/theme';

const API = API_BASE_URL;

interface Track {
  id: string;
  title: string;
  artist: string;
  duration_ms: number;
  bpm?: number;
}

interface MusicPlayerProps {
  compact?: boolean;
  onStateChange?: (playing: boolean) => void;
}

export function MusicPlayer({ compact = false, onStateChange }: MusicPlayerProps) {
  const { theme } = useTheme();
  const userId = useUserStore((s) => s.userId);
  const [playing, setPlaying] = useState(false);
  const [track, setTrack] = useState<Track | null>(null);
  const [playlist, setPlaylist] = useState<string | null>(null);

  useEffect(() => { fetchState(); }, []);

  async function fetchState() {
    try {
      const res = await fetch(`${API}/api/v1/music/state?user_id=${userId}`);
      if (res.ok) {
        const s = await res.json();
        setPlaying(s.is_playing);
        setTrack(s.current_track);
        setPlaylist(s.playlist_id);
      }
    } catch {}
  }

  async function togglePlay() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    const endpoint = playing ? 'pause' : 'resume';
    try {
      const res = await fetch(`${API}/api/v1/music/${endpoint}?user_id=${userId}`, { method: 'POST' });
      if (res.ok) {
        const s = await res.json();
        setPlaying(s.is_playing);
        onStateChange?.(s.is_playing);
      }
    } catch {}
  }

  async function nextTrack() {
    Haptics.selectionAsync();
    try {
      const res = await fetch(`${API}/api/v1/music/next?user_id=${userId}`, { method: 'POST' });
      if (res.ok) {
        const s = await res.json();
        if (s.current_track) setTrack(s.current_track);
      }
    } catch {}
  }

  async function startPreset(id: string) {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    try {
      const res = await fetch(`${API}/api/v1/music/play?user_id=${userId}&playlist_id=${id}`, { method: 'POST' });
      if (res.ok) {
        const s = await res.json();
        setPlaying(s.is_playing);
        setTrack(s.current_track);
        setPlaylist(id);
        onStateChange?.(true);
      }
    } catch {}
  }

  if (compact && !track) return null;

  if (!track) {
    return (
      <View style={styles.presetRow}>
        {['warmup', 'strength', 'hiit', 'cooldown'].map(id => (
          <TouchableOpacity key={id} style={[styles.presetBtn, { backgroundColor: theme.surface }]} onPress={() => startPreset(id)}>
            <Music size={14} color={theme.primary} />
            <Text style={[styles.presetText, { color: theme.primary }]}>{id}</Text>
          </TouchableOpacity>
        ))}
      </View>
    );
  }

  if (compact) {
    return (
      <View style={[styles.compactBar, { backgroundColor: theme.surface }]}>
        <TouchableOpacity onPress={togglePlay} style={[styles.compactPlay, { backgroundColor: theme.primary }]}>
          {playing ? <Pause size={16} color={theme.text} /> : <Play size={16} color={theme.text} />}
        </TouchableOpacity>
        <View style={styles.compactInfo}>
          <Text style={[styles.compactTitle, { color: theme.text }]} numberOfLines={1}>{track.title}</Text>
          <Text style={[styles.compactArtist, { color: theme.textMuted }]}>{track.artist}{track.bpm ? ` · ${track.bpm} BPM` : ''}</Text>
        </View>
        <TouchableOpacity onPress={nextTrack}>
          <SkipForward size={18} color={theme.textSecondary} />
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={[styles.card, { backgroundColor: theme.surface }]}>
      <View style={styles.header}>
        <Music size={16} color={theme.primary} />
        <Text style={[styles.headerTitle, { color: theme.textMuted }]}>Now Playing</Text>
      </View>
      <Text style={[styles.trackTitle, { color: theme.text }]}>{track.title}</Text>
      <Text style={[styles.trackArtist, { color: theme.textSecondary }]}>
        {track.artist}{track.bpm ? ` · ${track.bpm} BPM` : ''}
      </Text>
      <View style={styles.controls}>
        <TouchableOpacity onPress={nextTrack} style={styles.controlBtn}>
          <SkipBack size={20} color={theme.textSecondary} />
        </TouchableOpacity>
        <TouchableOpacity onPress={togglePlay} style={[styles.playBtn, { backgroundColor: theme.primary }]}>
          {playing ? <Pause size={24} color={theme.text} /> : <Play size={24} color={theme.text} />}
        </TouchableOpacity>
        <TouchableOpacity onPress={nextTrack} style={styles.controlBtn}>
          <SkipForward size={20} color={theme.textSecondary} />
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  presetRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
  presetBtn: {
    flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 4,
    borderRadius: 10, padding: 10,
  },
  presetText: { fontSize: 11, fontWeight: '500', textTransform: 'capitalize' },
  card: {
    borderRadius: 16, padding: 16, marginBottom: 12, alignItems: 'center',
  },
  header: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 12 },
  headerTitle: { fontSize: 12, fontWeight: '500' },
  trackTitle: { fontSize: 16, fontWeight: '600', marginBottom: 2 },
  trackArtist: { fontSize: 13, marginBottom: 16 },
  controls: { flexDirection: 'row', alignItems: 'center', gap: 24 },
  controlBtn: { padding: 8 },
  playBtn: {
    width: 56, height: 56, borderRadius: 28,
    alignItems: 'center', justifyContent: 'center',
  },
  compactBar: {
    flexDirection: 'row', alignItems: 'center',
    borderRadius: 12, padding: 10, gap: 10, marginBottom: 8,
  },
  compactPlay: { width: 32, height: 32, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  compactInfo: { flex: 1 },
  compactTitle: { fontSize: 13, fontWeight: '500' },
  compactArtist: { fontSize: 11 },
});
