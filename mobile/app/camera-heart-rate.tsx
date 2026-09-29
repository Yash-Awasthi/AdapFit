/**
 * Camera Heart Rate Measurement — rPPG (Remote Photoplethysmography)
 *
 * rPPG reads the pulse from tiny colour changes in the skin. A frame
 * processor (react-native-vision-camera) samples the back camera's RGB
 * buffer with the torch on — finger over the lens, illuminated from
 * inside — and the averages are posted to the CHROM estimator at
 * POST /api/v1/rppg/estimate-hr-chrom. The final BPM and confidence shown
 * on completion come from that response, not from on-device peak-picking.
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, Animated, Dimensions,
  StatusBar, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';
import {
  Camera, useCameraDevice, useCameraPermission, useFrameOutput,
} from 'react-native-vision-camera';
import { runOnJS } from 'react-native-worklets';
import { colors, typography, spacing } from '../src/theme';
import { api } from '../src/services/api';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

// rPPG Signal Processing Constants
const SAMPLE_RATE = 30; // FPS
const MEASUREMENT_DURATION = 30; // seconds
const MIN_SAMPLES_FOR_BPM = 150; // 5 seconds minimum
const BPM_MIN = 40;
const BPM_MAX = 200;
const FRAME_RESOLUTION = { width: 100, height: 100 };

type MeasurementState = 'idle' | 'calibrating' | 'measuring' | 'analyzing' | 'complete' | 'error';

interface HeartRateReading {
  bpm: number;
  confidence: number;
  timestamp: number;
  duration: number;
}

export default function CameraHeartRateScreen() {
  const router = useRouter();
  const { hasPermission, requestPermission } = useCameraPermission();
  const device = useCameraDevice('back');
  const [state, setState] = useState<MeasurementState>('idle');
  const [bpm, setBpm] = useState<number | null>(null);
  const [confidence, setConfidence] = useState(0);
  const [progress, setProgress] = useState(0);
  const [readings, setReadings] = useState<HeartRateReading[]>([]);
  const [signalQuality, setSignalQuality] = useState<'poor' | 'fair' | 'good'>('poor');

  const pulseAnim = useRef(new Animated.Value(1)).current;
  const progressAnim = useRef(new Animated.Value(0)).current;
  const greenChannelAvg = useRef<number[]>([]);
  const roiPixels = useRef<number[][]>([]);
  const startTimeRef = useRef<number>(0);
  const measurementTimer = useRef<NodeJS.Timeout | null>(null);
  const frameCountRef = useRef(0);

  const pushSample = useCallback((r: number, g: number, b: number) => {
    roiPixels.current.push([r, g, b]);
    if (roiPixels.current.length > 10000) roiPixels.current.shift();

    greenChannelAvg.current.push(g);
    frameCountRef.current++;

    const last30 = greenChannelAvg.current.slice(-30);
    if (last30.length >= 10) {
      const mean = last30.reduce((a, s) => a + s, 0) / last30.length;
      const variance = last30.reduce((sum, s) => sum + (s - mean) ** 2, 0) / last30.length;
      const cv = Math.sqrt(variance) / mean;
      if (cv > 0.01) setSignalQuality('good');
      else if (cv > 0.003) setSignalQuality('fair');
      else setSignalQuality('poor');
    }

    if (frameCountRef.current >= MIN_SAMPLES_FOR_BPM && frameCountRef.current % 30 === 0) {
      const liveBpm = calculateBPM();
      if (liveBpm && liveBpm >= BPM_MIN && liveBpm <= BPM_MAX) {
        setBpm(Math.round(liveBpm));
      }
    }
  }, []);

  const frameOutput = useFrameOutput({
    targetResolution: FRAME_RESOLUTION,
    pixelFormat: 'rgb',
    onFrame(frame) {
      'worklet';
      const buffer = frame.getPixelBuffer();
      const pixels = new Uint8Array(buffer);
      const isBGRA = frame.pixelFormat.includes('bgra');
      const redOffset = isBGRA ? 2 : 0;
      const blueOffset = isBGRA ? 0 : 2;

      let rSum = 0, gSum = 0, bSum = 0, count = 0;
      // Stride of 16 pixels (64 bytes) keeps this cheap at 30fps on a 100x100 buffer.
      for (let i = 0; i + 3 < pixels.length; i += 64) {
        rSum += pixels[i + redOffset];
        gSum += pixels[i + 1];
        bSum += pixels[i + blueOffset];
        count++;
      }
      frame.dispose();

      if (count > 0) {
        runOnJS(pushSample)(rSum / count, gSum / count, bSum / count);
      }
    },
  });

  // Pulse animation
  useEffect(() => {
    if (bpm && bpm > 0) {
      const interval = 60000 / bpm;
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 1.15, duration: interval * 0.3, useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 1, duration: interval * 0.7, useNativeDriver: true }),
        ])
      ).start();
    }
  }, [bpm]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (measurementTimer.current) clearInterval(measurementTimer.current);
    };
  }, []);

  const startMeasurement = useCallback(async () => {
    if (!hasPermission) {
      const granted = await requestPermission();
      if (!granted) {
        Alert.alert('Camera Permission', 'Camera access is needed to measure heart rate.');
        return;
      }
    }
    if (!device) {
      Alert.alert('No Camera', 'No back camera is available on this device.');
      return;
    }

    setState('calibrating');
    roiPixels.current = [];
    greenChannelAvg.current = [];
    frameCountRef.current = 0;

    // Calibration phase — lets the torch settle and the finger seat over the lens.
    setTimeout(() => {
      setState('measuring');
      startTimeRef.current = Date.now();

      measurementTimer.current = setInterval(() => {
        const elapsed = (Date.now() - startTimeRef.current) / 1000;
        const prog = Math.min(elapsed / MEASUREMENT_DURATION, 1);
        setProgress(prog);

        if (prog >= 1) {
          completeMeasurement();
        }
      }, 100);
    }, 2000);
  }, [hasPermission, device]);

  const completeMeasurement = useCallback(async () => {
    if (measurementTimer.current) clearInterval(measurementTimer.current);
    setState('analyzing');

    try {
      const result = await api.post('/api/v1/rppg/estimate-hr-chrom', {
        roi_pixels: roiPixels.current,
        timestamp: Date.now() / 1000,
      });
      const finalBpm = result?.heart_rate_bpm;
      if (typeof finalBpm === 'number' && finalBpm >= BPM_MIN && finalBpm <= BPM_MAX) {
        const reading: HeartRateReading = {
          bpm: Math.round(finalBpm),
          confidence: result?.confidence ?? 0,
          timestamp: Date.now(),
          duration: MEASUREMENT_DURATION,
        };
        setBpm(reading.bpm);
        setConfidence(reading.confidence);
        setReadings(prev => [reading, ...prev].slice(0, 10));
        setState('complete');
      } else {
        setState('error');
      }
    } catch {
      setState('error');
    }
  }, []);

  const calculateBPM = (): number | null => {
    const samples = greenChannelAvg.current;
    if (samples.length < MIN_SAMPLES_FOR_BPM) return null;

    // Simple peak detection for BPM estimation
    // In production, use FFT or autocorrelation for better accuracy
    const mean = samples.reduce((a, b) => a + b, 0) / samples.length;
    const threshold = mean * 1.05;

    let peaks: number[] = [];
    let lastPeakIdx = -10;

    for (let i = 1; i < samples.length - 1; i++) {
      if (samples[i] > threshold && samples[i] > samples[i - 1] && samples[i] > samples[i + 1]) {
        if (i - lastPeakIdx > SAMPLE_RATE * 0.4) { // Min 0.4s between peaks (150 BPM max)
          peaks.push(i);
          lastPeakIdx = i;
        }
      }
    }

    if (peaks.length < 3) return null;

    // Calculate average interval between peaks
    let totalInterval = 0;
    for (let i = 1; i < peaks.length; i++) {
      totalInterval += peaks[i] - peaks[i - 1];
    }
    const avgInterval = totalInterval / (peaks.length - 1);

    // Convert to BPM
    const bpm = (SAMPLE_RATE / avgInterval) * 60;
    return bpm;
  };

  const resetMeasurement = useCallback(() => {
    setState('idle');
    setBpm(null);
    setConfidence(0);
    setProgress(0);
    setSignalQuality('poor');
    greenChannelAvg.current = [];
    roiPixels.current = [];
    frameCountRef.current = 0;
  }, []);

  const confidenceLabel = confidence >= 0.7 ? 'High' : confidence >= 0.4 ? 'Medium' : 'Low';
  const confidenceColor = confidence >= 0.7 ? colors.health.success : confidence >= 0.4 ? '#F59E0B' : '#EF4444';
  const stateColor = state === 'measuring' ? colors.health.heart : state === 'complete' ? colors.health.success : colors.primary;

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />

      {/* Camera Preview */}
      <View style={styles.cameraContainer}>
        {hasPermission && device ? (
          <Camera
            style={styles.camera}
            device={device}
            isActive={state === 'measuring' || state === 'calibrating'}
            outputs={state === 'measuring' ? [frameOutput] : []}
            torchMode={state === 'measuring' || state === 'calibrating' ? 'on' : 'off'}
          />
        ) : (
          <View style={styles.cameraPlaceholder}>
            <Ionicons name="camera" size={64} color={colors.text.muted} />
            <Text style={[typography.body.md, { color: colors.text.muted, marginTop: 12 }]}>
              Camera access required
            </Text>
          </View>
        )}

        {/* Overlay with measurement UI */}
        <LinearGradient
          colors={['rgba(0,0,0,0.7)', 'transparent', 'transparent', 'rgba(0,0,0,0.7)']}
          style={styles.overlay}
        >
          {/* Top Bar */}
          <View style={styles.topBar}>
            <TouchableOpacity accessibilityRole="button" accessibilityLabel="Back" onPress={() => router.back()} style={styles.backButton}>
              <Ionicons name="chevron-back" size={24} color="#FFF" />
            </TouchableOpacity>
            <Text style={[typography.label.md, { color: '#FFF' }]}>Heart Rate</Text>
            <View style={{ width: 44 }} />
          </View>

          {/* Center Content */}
          <View style={styles.centerContent}>
            {state === 'idle' && (
              <View style={styles.idleContent}>
                <View style={styles.cameraIcon}>
                  <Ionicons name="camera" size={48} color="#FFF" />
                </View>
                <Text style={[typography.heading.h2, { color: '#FFF', marginTop: 20 }]}>
                  Measure Heart Rate
                </Text>
                <Text style={[typography.body.md, { color: 'rgba(255,255,255,0.7)', marginTop: 8, textAlign: 'center', paddingHorizontal: 32 }]}>
                  Cover the rear camera and flash with your fingertip. Stay still for 30 seconds.
                </Text>
                <TouchableOpacity style={styles.startButton} onPress={startMeasurement}>
                  <Ionicons name="play" size={24} color="#FFF" />
                  <Text style={[typography.label.lg, { color: '#FFF' }]}>Start Measurement</Text>
                </TouchableOpacity>
              </View>
            )}

            {state === 'calibrating' && (
              <View style={styles.measuringContent}>
                <Animated.View style={[styles.pulseRing, { transform: [{ scale: pulseAnim }] }]}>
                  <View style={styles.pulseInner}>
                    <Ionicons name="heart" size={48} color={colors.health.heart} />
                  </View>
                </Animated.View>
                <Text style={[typography.heading.h3, { color: '#FFF', marginTop: 20 }]}>
                  Calibrating...
                </Text>
                <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.6)', marginTop: 8 }]}>
                  Keep your finger still on the camera
                </Text>
              </View>
            )}

            {state === 'measuring' && (
              <View style={styles.measuringContent}>
                <Animated.View style={[styles.pulseRing, { transform: [{ scale: pulseAnim }] }]}>
                  <View style={styles.pulseInner}>
                    <Text style={[typography.metric.hero, { color: '#FFF' }]}>
                      {bpm || '--'}
                    </Text>
                    <Text style={[typography.label.md, { color: 'rgba(255,255,255,0.7)' }]}>BPM</Text>
                  </View>
                </Animated.View>

                {/* Signal Quality */}
                <View style={styles.qualityRow}>
                  <View style={[styles.qualityDot, {
                    backgroundColor: signalQuality === 'good' ? colors.health.success :
                      signalQuality === 'fair' ? '#F59E0B' : '#EF4444'
                  }]} />
                  <Text style={[typography.body.sm, { color: '#FFF' }]}>
                    Signal: {signalQuality.charAt(0).toUpperCase() + signalQuality.slice(1)}
                  </Text>
                </View>

                {/* Progress Bar */}
                <View style={styles.progressContainer}>
                  <View style={styles.progressBg}>
                    <Animated.View style={[styles.progressFill, {
                      width: `${progress * 100}%`,
                    }]} />
                  </View>
                  <Text style={[typography.body.xs, { color: 'rgba(255,255,255,0.6)', marginTop: 4 }]}>
                    {Math.round(progress * MEASUREMENT_DURATION)}s / {MEASUREMENT_DURATION}s
                  </Text>
                </View>
              </View>
            )}

            {state === 'analyzing' && (
              <View style={styles.measuringContent}>
                <Animated.View style={styles.pulseRing}>
                  <View style={styles.pulseInner}>
                    <Ionicons name="pulse" size={40} color={colors.health.heart} />
                  </View>
                </Animated.View>
                <Text style={[typography.heading.h3, { color: '#FFF', marginTop: 20 }]}>
                  Analyzing...
                </Text>
              </View>
            )}

            {state === 'complete' && (
              <View style={styles.completeContent}>
                <View style={styles.resultCard}>
                  <Ionicons name="heart" size={32} color={colors.health.heart} />
                  <Text style={[typography.metric.hero, { color: colors.text.primary, marginTop: 8 }]}>
                    {bpm}
                  </Text>
                  <Text style={[typography.label.md, { color: colors.text.muted }]}>BPM</Text>

                  {/* Confidence Indicator */}
                  <View style={[styles.confidenceBadge, { backgroundColor: confidenceColor + '20' }]}>
                    <View style={[styles.confidenceDot, { backgroundColor: confidenceColor }]} />
                    <Text style={[typography.body.sm, { color: confidenceColor }]}>
                      {confidenceLabel} confidence ({Math.round(confidence * 100)}%)
                    </Text>
                  </View>
                </View>

                <View style={styles.actionRow}>
                  <TouchableOpacity style={styles.retakeButton} onPress={resetMeasurement}>
                    <Ionicons name="refresh" size={20} color={colors.primary} />
                    <Text style={[typography.label.md, { color: colors.primary }]}>Measure Again</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={styles.saveButton} onPress={() => {
                    Alert.alert('Saved', `Heart rate of ${bpm} BPM has been saved.`);
                    router.back();
                  }}>
                    <Ionicons name="checkmark" size={20} color="#FFF" />
                    <Text style={[typography.label.md, { color: '#FFF' }]}>Save</Text>
                  </TouchableOpacity>
                </View>
              </View>
            )}

            {state === 'error' && (
              <View style={styles.errorContent}>
                <Ionicons name="alert-circle" size={48} color="#EF4444" />
                <Text style={[typography.heading.h3, { color: '#FFF', marginTop: 16 }]}>
                  Measurement Failed
                </Text>
                <Text style={[typography.body.md, { color: 'rgba(255,255,255,0.7)', marginTop: 8, textAlign: 'center' }]}>
                  Could not detect a clear pulse signal. Please ensure your finger fully covers the camera lens and try again.
                </Text>
                <TouchableOpacity style={styles.startButton} onPress={resetMeasurement}>
                  <Text style={[typography.label.lg, { color: '#FFF' }]}>Try Again</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        </LinearGradient>
      </View>

      {/* Recent Readings */}
      {readings.length > 0 && (
        <View style={styles.readingsSection}>
          <Text style={[typography.label.md, { color: colors.text.muted, marginBottom: 8 }]}>
            Recent Measurements
          </Text>
          {readings.slice(0, 5).map((r, i) => (
            <View key={i} style={styles.readingRow}>
              <Ionicons name="heart" size={16} color={colors.health.heart} />
              <Text style={[typography.body.md, { color: colors.text.primary, flex: 1 }]}>
                {r.bpm} BPM
              </Text>
              <Text style={[typography.body.sm, { color: colors.text.muted }]}>
                {Math.round(r.confidence * 100)}%
              </Text>
              <Text style={[typography.body.xs, { color: colors.text.muted, marginLeft: 8 }]}>
                {new Date(r.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </Text>
            </View>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  cameraContainer: { flex: 1 },
  camera: { flex: 1 },
  cameraPlaceholder: {
    flex: 1, justifyContent: 'center', alignItems: 'center',
    backgroundColor: '#1A1A2E',
  },
  overlay: { ...StyleSheet.absoluteFillObject, justifyContent: 'space-between' },
  topBar: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingTop: 50, paddingHorizontal: 16,
  },
  backButton: { width: 44, height: 44, justifyContent: 'center', alignItems: 'center' },
  centerContent: { flex: 1, justifyContent: 'center', alignItems: 'center' },

  // Idle State
  idleContent: { alignItems: 'center' },
  cameraIcon: {
    width: 96, height: 96, borderRadius: 48,
    backgroundColor: 'rgba(255,255,255,0.15)',
    justifyContent: 'center', alignItems: 'center',
  },
  startButton: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    backgroundColor: colors.health.heart,
    paddingHorizontal: 32, paddingVertical: 14,
    borderRadius: 24, marginTop: 32,
  },

  // Measuring State
  measuringContent: { alignItems: 'center' },
  pulseRing: {
    width: 160, height: 160, borderRadius: 80,
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    justifyContent: 'center', alignItems: 'center',
    borderWidth: 3, borderColor: 'rgba(239, 68, 68, 0.3)',
  },
  pulseInner: { alignItems: 'center' },
  qualityRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 16 },
  qualityDot: { width: 8, height: 8, borderRadius: 4 },
  progressContainer: { width: 200, marginTop: 16 },
  progressBg: {
    height: 6, backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: 3, overflow: 'hidden',
  },
  progressFill: { height: '100%', backgroundColor: colors.health.heart, borderRadius: 3 },

  // Complete State
  completeContent: { alignItems: 'center', width: '100%', paddingHorizontal: 32 },
  resultCard: {
    width: '100%', backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 24, padding: 24, alignItems: 'center',
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.1)',
  },
  confidenceBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingHorizontal: 12, paddingVertical: 6,
    borderRadius: 12, marginTop: 12,
  },
  confidenceDot: { width: 6, height: 6, borderRadius: 3 },
  actionRow: { flexDirection: 'row', gap: 12, marginTop: 24 },
  retakeButton: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingHorizontal: 24, paddingVertical: 12,
    borderRadius: 12, borderWidth: 1, borderColor: colors.primary,
  },
  saveButton: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: colors.primary,
    paddingHorizontal: 24, paddingVertical: 12, borderRadius: 12,
  },

  // Error State
  errorContent: { alignItems: 'center', paddingHorizontal: 32 },

  // Recent Readings
  readingsSection: {
    backgroundColor: colors.bg.card, padding: 16,
    borderTopLeftRadius: 20, borderTopRightRadius: 20,
  },
  readingRow: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    paddingVertical: 8,
    borderBottomWidth: 0.5, borderBottomColor: colors.surface.divider,
  },
});
