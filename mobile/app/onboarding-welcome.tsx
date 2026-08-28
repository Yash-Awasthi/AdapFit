import React, { useState } from 'react';
import { View, Text, TextInput, ScrollView, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { Heart, Dumbbell, Brain, MessageCircle } from 'lucide-react-native';
import { Button } from '../src/components';
import * as Haptics from 'expo-haptics';
import { API_BASE_URL } from '../src/services/config';
import { useUserStore } from '../src/stores';
import { useTheme } from '../src/services/theme';

const API = API_BASE_URL;

const FEATURES = [
  { icon: Heart, title: 'Recovery Tracking', desc: 'HRV, sleep, and subjective wellness scoring' },
  { icon: Dumbbell, title: 'Adaptive Workouts', desc: 'AI-generated based on your recovery state' },
  { icon: MessageCircle, title: 'AI Coach', desc: 'Context-aware fitness guidance' },
  { icon: Brain, title: 'Mental Health', desc: 'Mood tracking and breathing exercises' },
];

export default function OnboardingScreen() {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [gender, setGender] = useState('female');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const setUser = useUserStore((s) => s.setUser);
  const { theme } = useTheme();
  const s = makeStyles(theme);

  async function handleStart() {
    if (!email.trim()) {
      Alert.alert('Email required', 'Enter an email to continue.');
      return;
    }
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(),
          name: name.trim() || null,
          gender,
        }),
      });
      if (res.ok) {
        const user = await res.json();
        await setUser({
          id: user.id,
          email: user.email,
          name: user.name,
          gender: user.gender,
          fitness_level: user.fitness_level,
          primary_goal: user.primary_goal,
          preferred_days_per_week: user.preferred_days_per_week,
        });
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        router.replace('/(tabs)');
      } else {
        const detail = await res.text().catch(() => '');
        Alert.alert('Sign-up failed', `Server returned ${res.status}.${detail ? ` ${detail.slice(0, 200)}` : ''}`);
      }
    } catch (err: any) {
      Alert.alert('Could not reach the server', `${API_BASE_URL}\n\n${err?.message || String(err)}`);
    }
    setLoading(false);
  }

  return (
    <ScrollView style={s.container} contentContainerStyle={s.content}>
      {/* Logo */}
      <View style={s.logoContainer}>
        <View style={s.logoIcon}>
          <Text style={s.logoEmoji}>⚡</Text>
        </View>
        <Text style={s.title}>AdapFit</Text>
        <Text style={s.subtitle}>AI-Powered Adaptive Fitness</Text>
      </View>

      {/* Features */}
      <View style={s.features}>
        {FEATURES.map((f, i) => (
          <View key={i} style={s.feature}>
            <f.icon size={20} color={theme.primaryLight} />
            <View style={s.featureText}>
              <Text style={s.featureTitle}>{f.title}</Text>
              <Text style={s.featureDesc}>{f.desc}</Text>
            </View>
          </View>
        ))}
      </View>

      {/* Form */}
      <View style={s.form}>
        <Text style={s.label}>Name (optional)</Text>
        <TextInput
          style={s.input}
          value={name}
          onChangeText={setName}
          placeholder="Alex Johnson"
          placeholderTextColor="#475569"
          autoCapitalize="words"
        />
        <Text style={s.label}>Email</Text>
        <TextInput
          style={s.input}
          value={email}
          onChangeText={setEmail}
          placeholder="your@email.com"
          placeholderTextColor="#475569"
          keyboardType="email-address"
          autoCapitalize="none"
        />
        <Text style={s.label}>Gender</Text>
        <View style={s.genderRow}>
          {['female', 'male', 'other'].map((g) => (
            <TouchableOpacity
              key={g}
              onPress={() => { Haptics.selectionAsync(); setGender(g); }}
              style={[s.genderChip, gender === g && s.genderChipActive]}
            >
              <Text style={[s.genderChipText, gender === g && s.genderChipTextActive]}>
                {g}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
        <Button
          title="Get Started"
          onPress={handleStart}
          loading={loading}
        />
      </View>

      <Text style={s.footer}>
        Free, open-source, no account required.
      </Text>
    </ScrollView>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.background },
    content: { padding: 32, paddingTop: 80, paddingBottom: 40 },
    logoContainer: { alignItems: 'center', marginBottom: 40 },
    logoIcon: {
      width: 64, height: 64, borderRadius: 20,
      backgroundColor: theme.primaryBg,
      alignItems: 'center', justifyContent: 'center', marginBottom: 16,
    },
    logoEmoji: { fontSize: 32 },
    title: { fontSize: 36, fontWeight: '800', color: theme.text, marginBottom: 8 },
    subtitle: { fontSize: 16, color: theme.textMuted },
    features: { marginBottom: 32 },
    feature: {
      flexDirection: 'row', alignItems: 'center', gap: 12,
      paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: theme.border,
    },
    featureText: { flex: 1 },
    featureTitle: { fontSize: 15, fontWeight: '600', color: theme.text },
    featureDesc: { fontSize: 12, color: theme.textMuted, marginTop: 2 },
    form: { gap: 12, marginBottom: 24 },
    label: { fontSize: 14, color: theme.textSecondary, marginBottom: 4 },
    input: {
      backgroundColor: theme.surface, borderRadius: 12, padding: 16,
      fontSize: 16, color: theme.text, marginBottom: 12,
    },
    genderRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
    genderChip: {
      flex: 1,
      paddingVertical: 12,
      borderRadius: 12,
      backgroundColor: theme.surface,
      borderWidth: 1,
      borderColor: theme.border,
      alignItems: 'center',
    },
    genderChipActive: { backgroundColor: theme.primary, borderColor: theme.primary },
    genderChipText: { fontSize: 14, color: theme.textSecondary, textTransform: 'capitalize' },
    genderChipTextActive: { color: '#fff', fontWeight: '700' },
    footer: { fontSize: 12, color: '#475569', textAlign: 'center' },
  });
}
