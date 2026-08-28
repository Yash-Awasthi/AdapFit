/**
 * Smart Music Player — Phase-aware playlist with BPM visualization.
 * Switches playlists based on workout phase (warmup/main/cooldown).
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Easing,
} from 'react-native';
import {
  Play, Pause, SkipForward, SkipBack, Music,
  Volume2, Zap, Snowflake, Flame,
} from 'lucide-react-native';
import * as Haptics from 'expo-haptics';
import { API_BASE_URL } from '../services/config';

interface Track {
  title: string;
  artist: string;
  bpm: number;
  genre: string;
  energy: number;
}

interface PhasePlaylist {
  phase: string;
  name: string;
  tracks: Track[];
  target_bpm: number;
  track_count: number;
}

interface SmartMusicPlayerProps {
  workoutType?: string;
  durationMinutes?: number;
  currentSet?: number;
  totalSets?: number;
  compact?: boolean;
}

const PHASE_CONFIG = {
  warmup: { color: '#F59E0B', icon: Flame, label: 'Warmup' },
  main: { color: '#EF4444', icon: Zap, label: 'Power' },
  cooldown: { color: '#38BDF8', icon: Snowflake, label: 'Cooldown' },
};

export function SmartMusicPlayer({
  workoutType = 'strength',
  durationMinutes = 45,
  currentSet = 1,
  totalSets = 12,
  compact = false,
}: SmartMusicPlayerProps) {
  const [playlists, setPlaylists] = useState<PhasePlaylist[]>([]);
  const [currentPhase, setCurrentPhase] = useState('warmup');
  const [trackIndex, setTrackIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [loading, setLoading] = useState(true);
  const bpmPulse = useRef(new Animated.Value(1)).current;

  // Determine phase from set progress
  useEffect(() => {
    const progress = currentSet / Math.max(1, totalSets);
    if (progress < 0.15) setCurrentPhase('warmup');
    else if (progress > 0.85) setCurrentPhase('cooldown');
    else setCurrentPhase('main');
  }, [currentSet, totalSets]);

  // BPM pulse animation
  useEffect(() => {
    if (isPlaying) {
      const bpm = getCurrentTrack()?.bpm || 120;
      const pulseInterval = 60000 / bpm; // ms per beat
      const pulse = Animated.loop(
        Animated.sequence([
          Animated.timing(bpmPulse, {
            toValue: 1.08,
            duration: pulseInterval / 2,
            easing: Easing.out(Easing.ease),
            useNativeDriver: true,
          }),
          Animated.timing(bpmPulse, {
            toValue: 1,
            duration: pulseInterval / 2,
            easing: Easing.in(Easing.ease),
            useNativeDriver: true,
          }),
        ])
      );
      pulse.start();
      return () => pulse.stop();
    }
  }, [isPlaying, trackIndex, currentPhase]);

  // Fetch playlist on mount
  useEffect(() => {
    fetchPlaylist();
  }, []);

  async function fetchPlaylist() {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/music-playlists/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workout_type: workoutType,
          duration_minutes: durationMinutes,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setPlaylists(data.phases || []);
      }
    } catch {
      // Use built-in fallback playlists
      setPlaylists([
        {
          phase: 'warmup', name: 'Warmup', target_bpm: 110, track_count: 3,
          tracks: [
            { title: 'Morning Warmup', artist: 'AdapFit', bpm: 105, genre: 'lofi', energy: 0.3 },
            { title: 'Easy Flow', artist: 'AdapFit', bpm: 110, genre: 'ambient', energy: 0.35 },
            { title: 'Ramp Up', artist: 'AdapFit', bpm: 115, genre: 'electronic', energy: 0.4 },
          ],
        },
        {
          phase: 'main', name: 'Power', target_bpm: 145, track_count: 5,
          tracks: [
            { title: 'Beast Mode', artist: 'AdapFit', bpm: 150, genre: 'edm', energy: 0.9 },
            { title: 'Heavy Lifting', artist: 'AdapFit', bpm: 140, genre: 'hiphop', energy: 0.85 },
            { title: 'Power Surge', artist: 'AdapFit', bpm: 155, genre: 'drumnbass', energy: 0.95 },
            { title: 'Iron Will', artist: 'AdapFit', bpm: 135, genre: 'rock', energy: 0.8 },
            { title: 'PR Energy', artist: 'AdapFit', bpm: 148, genre: 'edm', energy: 0.93 },
          ],
        },
        {
          phase: 'cooldown', name: 'Cooldown', target_bpm: 88, track_count: 3,
          tracks: [
            { title: 'Cool Down', artist: 'AdapFit', bpm: 85, genre: 'ambient', energy: 0.15 },
            { title: 'Deep Breath', artist: 'AdapFit', bpm: 90, genre: 'chill', energy: 0.2 },
            { title: 'Stretch Out', artist: 'AdapFit', bpm: 80, genre: 'lofi', energy: 0.1 },
          ],
        },
      ]);
    }
    setLoading(false);
  }

  function getCurrentPlaylist() {
    return playlists.find((p) => p.phase === currentPhase) || playlists[0];
  }

  function getCurrentTrack() {
    const playlist = getCurrentPlaylist();
    if (!playlist || !playlist.tracks[trackIndex]) return null;
    return playlist.tracks[trackIndex];
  }

  function nextTrack() {
    Haptics.selectionAsync();
    const playlist = getCurrentPlaylist();
    if (!playlist) return;
    setTrackIndex((i) => (i + 1) % playlist.tracks.length);
  }

  function prevTrack() {
    Haptics.selectionAsync();
    const playlist = getCurrentPlaylist();
    if (!playlist) return;
    setTrackIndex((i) => (i - 1 + playlist.tracks.length) % playlist.tracks.length);
  }

  const track = getCurrentTrack();
  const phaseConfig = PHASE_CONFIG[currentPhase as keyof typeof PHASE_CONFIG];
  const PhaseIcon = phaseConfig?.icon || Music;

  if (loading || !track) {
    return (
      <View style={[styles.container, compact && styles.containerCompact]}>
        <Text style={styles.loadingText}>Loading playlist...</Text>
      </View>
    );
  }

  if (compact) {
    return (
      <View style={styles.containerCompact}>
        <View style={styles.compactRow}>
          <Animated.View style={{ transform: [{ scale: bpmPulse }] }}>
            <View style={[styles.phaseDot, { backgroundColor: phaseConfig.color }]}>
              <PhaseIcon size={12} color="#fff" />
            </View>
          </Animated.View>
          <View style={styles.compactInfo}>
            <Text style={styles.compactTitle} numberOfLines={1}>{track.title}</Text>
            <Text style={styles.compactBpm}>{track.bpm} BPM</Text>
          </View>
          <TouchableOpacity onPress={() => setIsPlaying(!isPlaying)} style={styles.compactPlay}>
            {isPlaying ? (
              <Pause size={14} color="#F8FAFC" />
            ) : (
              <Play size={14} color="#F8FAFC" />
            )}
          </TouchableOpacity>
          <TouchableOpacity onPress={nextTrack} style={styles.compactPlay}>
            <SkipForward size={14} color="#94A3B8" />
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Phase Indicator */}
      <View style={styles.phaseRow}>
        {playlists.map((p) => {
          const cfg = PHASE_CONFIG[p.phase as keyof typeof PHASE_CONFIG];
          const Icon = cfg?.icon || Music;
          const isActive = p.phase === currentPhase;
          return (
            <View
              key={p.phase}
              style={[styles.phaseChip, isActive && { backgroundColor: cfg.color + '30', borderColor: cfg.color }]}
            >
              <Icon size={12} color={isActive ? cfg.color : '#8B96AB'} />
              <Text style={[styles.phaseChipText, isActive && { color: cfg.color }]}>
                {cfg?.label || p.phase}
              </Text>
            </View>
          );
        })}
      </View>

      {/* Track Info */}
      <View style={styles.trackInfo}>
        <Animated.View style={[styles.albumArt, { transform: [{ scale: bpmPulse }] }]}>
          <Music size={32} color={phaseConfig.color} />
        </Animated.View>
        <View style={styles.trackDetails}>
          <Text style={styles.trackTitle}>{track.title}</Text>
          <Text style={styles.trackArtist}>{track.artist}</Text>
          <View style={styles.bpmRow}>
            <Text style={styles.bpmValue}>{track.bpm}</Text>
            <Text style={styles.bpmLabel}>BPM</Text>
            <View style={styles.energyBar}>
              <View style={[styles.energyFill, { width: `${track.energy * 100}%`, backgroundColor: phaseConfig.color }]} />
            </View>
          </View>
        </View>
      </View>

      {/* Controls */}
      <View style={styles.controls}>
        <TouchableOpacity onPress={prevTrack} style={styles.controlBtn}>
          <SkipBack size={20} color="#CBD5E1" />
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.playBtn, { backgroundColor: phaseConfig.color }]}
          onPress={() => {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
            setIsPlaying(!isPlaying);
          }}
        >
          {isPlaying ? (
            <Pause size={24} color="#fff" />
          ) : (
            <Play size={24} color="#fff" />
          )}
        </TouchableOpacity>
        <TouchableOpacity onPress={nextTrack} style={styles.controlBtn}>
          <SkipForward size={20} color="#CBD5E1" />
        </TouchableOpacity>
      </View>

      {/* Track List */}
      <View style={styles.trackList}>
        {getCurrentPlaylist()?.tracks.map((t, i) => (
          <TouchableOpacity
            key={i}
            style={[styles.trackItem, i === trackIndex && styles.trackItemActive]}
            onPress={() => {
              Haptics.selectionAsync();
              setTrackIndex(i);
            }}
          >
            <Text style={[styles.trackItemBpm, i === trackIndex && { color: phaseConfig.color }]}>
              {t.bpm}
            </Text>
            <Text style={[styles.trackItemTitle, i === trackIndex && { color: '#F8FAFC' }]} numberOfLines={1}>
              {t.title}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 16,
    marginTop: 12,
  },
  containerCompact: {
    backgroundColor: '#1E293B',
    borderRadius: 10,
    padding: 8,
  },
  loadingText: { color: '#8B96AB', textAlign: 'center', padding: 12 },

  // Compact mode
  compactRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  phaseDot: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  compactInfo: { flex: 1 },
  compactTitle: { fontSize: 13, fontWeight: '600', color: '#F8FAFC' },
  compactBpm: { fontSize: 11, color: '#8B96AB' },
  compactPlay: { padding: 6 },

  // Full mode
  phaseRow: { flexDirection: 'row', gap: 8, marginBottom: 16 },
  phaseChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    backgroundColor: '#0F172A',
    borderWidth: 1,
    borderColor: '#334155',
  },
  phaseChipText: { fontSize: 11, fontWeight: '600', color: '#8B96AB' },

  trackInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    marginBottom: 16,
  },
  albumArt: {
    width: 64,
    height: 64,
    borderRadius: 12,
    backgroundColor: '#0F172A',
    alignItems: 'center',
    justifyContent: 'center',
  },
  trackDetails: { flex: 1 },
  trackTitle: { fontSize: 16, fontWeight: '700', color: '#F8FAFC' },
  trackArtist: { fontSize: 13, color: '#8B96AB', marginBottom: 4 },
  bpmRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  bpmValue: { fontSize: 18, fontWeight: '800', color: '#F8FAFC' },
  bpmLabel: { fontSize: 10, color: '#8B96AB', fontWeight: '600' },
  energyBar: {
    flex: 1,
    height: 4,
    backgroundColor: '#334155',
    borderRadius: 2,
    marginLeft: 8,
    overflow: 'hidden',
  },
  energyFill: { height: 4, borderRadius: 2 },

  controls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 24,
    marginBottom: 16,
  },
  controlBtn: { padding: 8 },
  playBtn: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
  },

  trackList: { borderTopWidth: 1, borderTopColor: '#334155', paddingTop: 8 },
  trackItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 6,
    paddingHorizontal: 8,
    borderRadius: 6,
  },
  trackItemActive: { backgroundColor: '#0F172A' },
  trackItemBpm: { fontSize: 11, color: '#8B96AB', fontWeight: '600', width: 30 },
  trackItemTitle: { fontSize: 12, color: '#CBD5E1', flex: 1 },
});
