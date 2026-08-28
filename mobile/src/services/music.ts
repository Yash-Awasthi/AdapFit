/**
 * Workout Music Integration
 * 
 * Controls Spotify and Apple Music playback during workouts.
 * Falls back to a no-op on web/dev environments.
 * 
 * Uses:
 * - Spotify: expo-av for local playback, deep links for Spotify app
 * - Apple Music: expo-av native module
 */
import { Platform, Linking } from 'react-native';

export interface Track {
  id: string;
  title: string;
  artist: string;
  duration_ms: number;
  uri?: string; // Spotify URI or local file URI
}

export interface MusicState {
  isPlaying: boolean;
  currentTrack: Track | null;
  playlist: Track[];
  volume: number; // 0-1
  provider: 'spotify' | 'apple_music' | 'none';
}

// Default workout playlists (curated BPM ranges)
const WORKOUT_PRESETS: Record<string, Track[]> = {
  warmup: [
    { id: 'w1', title: 'Loosen Up', artist: 'AdapFit', duration_ms: 210000 },
    { id: 'w2', title: 'Easy Flow', artist: 'AdapFit', duration_ms: 240000 },
  ],
  strength: [
    { id: 's1', title: 'Heavy Lifter', artist: 'AdapFit', duration_ms: 195000 },
    { id: 's2', title: 'Power Surge', artist: 'AdapFit', duration_ms: 180000 },
    { id: 's3', title: 'Iron Will', artist: 'AdapFit', duration_ms: 210000 },
  ],
  hiit: [
    { id: 'h1', title: 'Sprint Mode', artist: 'AdapFit', duration_ms: 165000 },
    { id: 'h2', title: 'Interval Madness', artist: 'AdapFit', duration_ms: 150000 },
    { id: 'h3', title: 'Cardio Blast', artist: 'AdapFit', duration_ms: 170000 },
  ],
  cooldown: [
    { id: 'c1', title: 'Wind Down', artist: 'AdapFit', duration_ms: 270000 },
    { id: 'c2', title: 'Stretch & Breathe', artist: 'AdapFit', duration_ms: 300000 },
  ],
};

let Audio: any = null;
try {
  Audio = require('expo-av').Audio;
} catch {}

class MusicService {
  private state: MusicState = {
    isPlaying: false,
    currentTrack: null,
    playlist: [],
    volume: 0.7,
    provider: 'none',
  };
  private listeners: ((state: MusicState) => void)[] = [];

  /**
   * Detect available music provider.
   */
  async detectProvider(): Promise<'spotify' | 'apple_music' | 'none'> {
    if (Platform.OS === 'ios') {
      // Check if Apple Music is available
      try {
        const canOpen = await Linking.canOpenURL('music://');
        if (canOpen) {
          this.state.provider = 'apple_music';
          return 'apple_music';
        }
      } catch {}
    }

    // Check Spotify
    try {
      const canSpotify = await Linking.canOpenURL('spotify://');
      if (canSpotify) {
        this.state.provider = 'spotify';
        return 'spotify';
      }
    } catch {}

    this.state.provider = 'none';
    return 'none';
  }

  /**
   * Load a preset workout playlist.
   */
  loadPreset(preset: keyof typeof WORKOUT_PRESETS) {
    this.state.playlist = [...(WORKOUT_PRESETS[preset] || [])];
    this.notify();
  }

  /**
   * Load a custom playlist.
   */
  loadPlaylist(tracks: Track[]) {
    this.state.playlist = [...tracks];
    this.notify();
  }

  /**
   * Play the current or specified track.
   */
  async play(track?: Track) {
    const t = track || this.state.playlist[0];
    if (!t) return;

    this.state.currentTrack = t;
    this.state.isPlaying = true;

    // Deep link to Spotify/Apple Music if available
    if (this.state.provider === 'spotify' && t.uri?.startsWith('spotify:')) {
      try {
        await Linking.openURL(t.uri);
      } catch {}
    } else if (this.state.provider === 'apple_music' && t.uri) {
      try {
        await Linking.openURL(`music://${t.uri}`);
      } catch {}
    }
    // Otherwise, expo-av would handle local playback
    // For now, we track state only

    this.notify();
  }

  async pause() {
    this.state.isPlaying = false;
    this.notify();
  }

  async resume() {
    if (this.state.currentTrack) {
      this.state.isPlaying = true;
      this.notify();
    }
  }

  async stop() {
    this.state.isPlaying = false;
    this.state.currentTrack = null;
    this.notify();
  }

  async next() {
    const { playlist, currentTrack } = this.state;
    if (!currentTrack || playlist.length === 0) return;
    const idx = playlist.findIndex(t => t.id === currentTrack.id);
    const next = playlist[(idx + 1) % playlist.length];
    await this.play(next);
  }

  async previous() {
    const { playlist, currentTrack } = this.state;
    if (!currentTrack || playlist.length === 0) return;
    const idx = playlist.findIndex(t => t.id === currentTrack.id);
    const prev = playlist[(idx - 1 + playlist.length) % playlist.length];
    await this.play(prev);
  }

  setVolume(vol: number) {
    this.state.volume = Math.max(0, Math.min(1, vol));
    this.notify();
  }

  getState(): MusicState {
    return { ...this.state };
  }

  subscribe(listener: (state: MusicState) => void) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notify() {
    for (const l of this.listeners) l({ ...this.state });
  }
}

export const musicService = new MusicService();
export { WORKOUT_PRESETS };
