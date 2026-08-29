/**
 * YouTube surface for content cards.
 *
 * Plays inline when react-native-webview is installed, and otherwise renders
 * the real YouTube thumbnail and hands the tap to the YouTube app. Keeping the
 * dependency optional means the feed works on the current build without a
 * native rebuild.
 */
import React, { useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, ActivityIndicator, Linking,
  NativeModules, UIManager,
} from 'react-native';
import { Image } from 'expo-image';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, spacing, radius } from '../theme';

let WebView: any = null;
try {
  // The JavaScript package resolves as soon as it is installed, but the view
  // only renders once the native module is linked by a rebuild. Requiring
  // both means a pending `expo run:android` degrades to the external opener
  // instead of crashing the card.
  const nativeLinked = Boolean(
    NativeModules.RNCWebView || NativeModules.RNCWebViewModule || UIManager.getViewManagerConfig?.('RNCWebView')
  );
  if (nativeLinked) WebView = require('react-native-webview').WebView;
} catch {
  WebView = null;
}

export const inlinePlaybackAvailable = WebView !== null;

export interface VideoMedia {
  videoId?: string | null;
  thumbnailUrl?: string | null;
  embedUrl?: string | null;
  watchUrl?: string | null;
  searchUrl?: string | null;
  gifUrl?: string | null;
}

interface Props extends VideoMedia {
  title: string;
  /** Accent used by the poster fallback when there is no image to show. */
  accent?: string;
  icon?: string;
  height?: number;
  durationSeconds?: number;
}

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export function VideoCard({
  title, videoId, thumbnailUrl, embedUrl, watchUrl, searchUrl, gifUrl,
  accent = colors.primary, icon = 'play', height = 190, durationSeconds,
}: Props) {
  const [playing, setPlaying] = useState(false);
  const canPlayInline = inlinePlaybackAvailable && !!embedUrl;
  const externalUrl = watchUrl || searchUrl;
  const poster = thumbnailUrl || gifUrl;

  const open = () => {
    if (canPlayInline) {
      setPlaying(true);
      return;
    }
    if (externalUrl) Linking.openURL(externalUrl);
  };

  if (playing && canPlayInline) {
    return (
      <View style={[styles.frame, { height }]}>
        <WebView
          source={{ uri: embedUrl }}
          style={styles.webview}
          allowsInlineMediaPlayback
          mediaPlaybackRequiresUserAction={false}
          startInLoadingState
          renderLoading={() => (
            <View style={styles.loading}>
              <ActivityIndicator color={colors.primary} />
            </View>
          )}
        />
      </View>
    );
  }

  return (
    <TouchableOpacity
      style={[styles.frame, { height }]}
      onPress={open}
      activeOpacity={0.9}
      accessibilityRole="button"
      accessibilityLabel={`Play ${title}`}
    >
      {poster ? (
        <Image
          source={{ uri: poster }}
          style={StyleSheet.absoluteFill}
          contentFit="cover"
          transition={200}
        />
      ) : (
        <LinearGradient
          colors={[accent + 'CC', colors.bg.elevated]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={StyleSheet.absoluteFill}
        >
          <View style={styles.posterIcon}>
            <Ionicons name={icon as any} size={40} color="rgba(255,255,255,0.85)" />
          </View>
        </LinearGradient>
      )}

      {/* Keeps the play control and badges legible over any thumbnail. */}
      <LinearGradient
        colors={['rgba(0,0,0,0.05)', 'rgba(0,0,0,0.55)']}
        style={StyleSheet.absoluteFill}
      />

      <View style={styles.playBadge}>
        <Ionicons name="play" size={22} color="#FFF" style={{ marginLeft: 3 }} />
      </View>

      {durationSeconds ? (
        <View style={styles.metaBadge}>
          <Ionicons name="time-outline" size={11} color="#FFF" />
          <Text style={styles.metaBadgeText}>{formatDuration(durationSeconds)}</Text>
        </View>
      ) : null}

      {!videoId && externalUrl ? (
        <View style={[styles.metaBadge, styles.searchBadge]}>
          <Ionicons name="logo-youtube" size={11} color="#FFF" />
          <Text style={styles.metaBadgeText}>Search</Text>
        </View>
      ) : null}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  frame: {
    width: '100%',
    borderRadius: radius.lg,
    overflow: 'hidden',
    backgroundColor: colors.bg.elevated,
    justifyContent: 'center',
    alignItems: 'center',
  },
  webview: { flex: 1, width: '100%', backgroundColor: '#000' },
  loading: { ...StyleSheet.absoluteFillObject, justifyContent: 'center', alignItems: 'center' },
  posterIcon: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  playBadge: {
    width: 56, height: 56, borderRadius: 28,
    backgroundColor: 'rgba(0,0,0,0.55)',
    borderWidth: 2, borderColor: 'rgba(255,255,255,0.85)',
    justifyContent: 'center', alignItems: 'center',
  },
  metaBadge: {
    position: 'absolute', bottom: spacing.sm, right: spacing.sm,
    flexDirection: 'row', alignItems: 'center', gap: 4,
    backgroundColor: 'rgba(0,0,0,0.7)',
    paddingHorizontal: spacing.sm, paddingVertical: 3,
    borderRadius: radius.xs,
  },
  searchBadge: { right: undefined, left: spacing.sm },
  metaBadgeText: { fontSize: 11, color: '#FFF', fontWeight: '600' },
});
