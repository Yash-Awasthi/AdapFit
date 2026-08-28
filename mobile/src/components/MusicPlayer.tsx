import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Play, Pause, SkipForward, SkipBack, Music } from 'lucide-react-native';
import * as Haptics from 'expo-haptics';
import { API_BASE_URL } from '../services/config';
import { useUserStore } from '../stores';

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
          <TouchableOpacity key={id} style={styles.presetBtn} onPress={() => startPreset(id)}>
            <Music size={14} color="#818CF8" />
            <Text style={styles.presetText}>{id}</Text>
          </TouchableOpacity>
        ))}
      </View>
    );
  }

  if (compact) {
    return (
      <View style={styles.compactBar}>
        <TouchableOpacity onPress={togglePlay} style={styles.compactPlay}>
          {playing ? <Pause size={16} color="#F8FAFC" /> : <Play size={16} color="#F8FAFC" />}
        </TouchableOpacity>
        <View style={styles.compactInfo}>
          <Text style={styles.compactTitle} numberOfLines={1}>{track.title}</Text>
          <Text style={styles.compactArtist}>{track.artist}{track.bpm ? ` · ${track.bpm} BPM` : ''}</Text>
        </View>
        <TouchableOpacity onPress={nextTrack}>
          <SkipForward size={18} color="#94A3B8" />
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Music size={16} color="#818CF8" />
        <Text style={styles.headerTitle}>Now Playing</Text>
      </View>
      <Text style={styles.trackTitle}>{track.title}</Text>
      <Text style={styles.trackArtist}>
        {track.artist}{track.bpm ? ` · ${track.bpm} BPM` : ''}
      </Text>
      <View style={styles.controls}>
        <TouchableOpacity onPress={nextTrack} style={styles.controlBtn}>
          <SkipBack size={20} color="#94A3B8" />
        </TouchableOpacity>
        <TouchableOpacity onPress={togglePlay} style={styles.playBtn}>
          {playing ? <Pause size={24} color="#F8FAFC" /> : <Play size={24} color="#F8FAFC" />}
        </TouchableOpacity>
        <TouchableOpacity onPress={nextTrack} style={styles.controlBtn}>
          <SkipForward size={20} color="#94A3B8" />
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  presetRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
  presetBtn: {
    flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 4,
    backgroundColor: '#1E293B', borderRadius: 10, padding: 10,
  },
  presetText: { fontSize: 11, color: '#818CF8', fontWeight: '500', textTransform: 'capitalize' },
  card: {
    backgroundColor: '#1E293B', borderRadius: 16, padding: 16, marginBottom: 12, alignItems: 'center',
  },
  header: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 12 },
  headerTitle: { fontSize: 12, color: '#8B96AB', fontWeight: '500' },
  trackTitle: { fontSize: 16, fontWeight: '600', color: '#F8FAFC', marginBottom: 2 },
  trackArtist: { fontSize: 13, color: '#94A3B8', marginBottom: 16 },
  controls: { flexDirection: 'row', alignItems: 'center', gap: 24 },
  controlBtn: { padding: 8 },
  playBtn: {
    width: 56, height: 56, borderRadius: 28, backgroundColor: '#4F46E5',
    alignItems: 'center', justifyContent: 'center',
  },
  compactBar: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#1E293B',
    borderRadius: 12, padding: 10, gap: 10, marginBottom: 8,
  },
  compactPlay: { width: 32, height: 32, borderRadius: 16, backgroundColor: '#4F46E5', alignItems: 'center', justifyContent: 'center' },
  compactInfo: { flex: 1 },
  compactTitle: { fontSize: 13, fontWeight: '500', color: '#F8FAFC' },
  compactArtist: { fontSize: 11, color: '#8B96AB' },
});
