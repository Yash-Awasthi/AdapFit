/**
 * Register Screen — Premium signup UI
 */
import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, KeyboardAvoidingView, Platform, ActivityIndicator, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, radius, presets } from '../src/theme';

import { API_V1 as API } from '../src/services/config';
import { setToken } from '../src/services/authToken';
import { useUserStore } from '../src/stores';
export default function RegisterScreen() {
  const router = useRouter();
  const setUser = useUserStore((s) => s.setUser);
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleRegister = async () => {
    if (!displayName.trim() || !email.trim() || !username.trim() || !password) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }
    if (password !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match');
      return;
    }
    if (password.length < 8) {
      Alert.alert('Error', 'Password must be at least 8 characters');
      return;
    }
    setLoading(true);
    try {
      const r = await fetch(`${API}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), username: username.trim(), password, display_name: displayName.trim() }),
      });
      const data = await r.json();
      if (r.ok && data.tokens) {
        await setToken(data.tokens.access_token ?? null);
        // The root layout bounces to onboarding when the store has no profile.
        if (data.user?.id) {
          await setUser({
            id: data.user.id,
            email: data.user.email,
            name: data.user.display_name ?? data.user.username ?? null,
          });
        }
        router.replace('/(tabs)');
      } else {
        Alert.alert('Registration Failed', data.detail || data.error || 'Please try again');
      }
    } catch {
      Alert.alert('Error', 'Network error. Please try again.');
    }
    setLoading(false);
  };

  const passwordStrength = (pw: string) => {
    let score = 0;
    if (pw.length >= 8) score++;
    if (pw.length >= 12) score++;
    if (/[A-Z]/.test(pw)) score++;
    if (/[0-9]/.test(pw)) score++;
    if (/[^A-Za-z0-9]/.test(pw)) score++;
    return score;
  };

  const strength = passwordStrength(password);
  const strengthColors = ['#EF4444', '#F97316', '#EAB308', '#22C55E', '#10B981'];
  const strengthLabels = ['Very Weak', 'Weak', 'Fair', 'Strong', 'Very Strong'];

  return (
    <KeyboardAvoidingView style={ns.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView contentContainerStyle={ns.scrollContent} showsVerticalScrollIndicator={false}>
        <TouchableOpacity style={ns.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={colors.text.primary} />
        </TouchableOpacity>

        <View style={ns.header}>
          <Text style={ns.title}>Create Account</Text>
          <Text style={ns.subtitle}>Join AdapFit and start your health journey</Text>
        </View>

        <View style={ns.form}>
          <View style={ns.inputGroup}>
            <Text style={ns.label}>Full Name</Text>
            <View style={ns.inputRow}>
              <Ionicons name="person-outline" size={20} color={colors.text.muted} />
              <TextInput style={ns.input} value={displayName} onChangeText={setDisplayName} placeholder="John Doe" placeholderTextColor={colors.text.muted} autoCapitalize="words" />
            </View>
          </View>

          <View style={ns.inputGroup}>
            <Text style={ns.label}>Email</Text>
            <View style={ns.inputRow}>
              <Ionicons name="mail-outline" size={20} color={colors.text.muted} />
              <TextInput style={ns.input} value={email} onChangeText={setEmail} placeholder="you@example.com" placeholderTextColor={colors.text.muted} keyboardType="email-address" autoCapitalize="none" />
            </View>
          </View>

          <View style={ns.inputGroup}>
            <Text style={ns.label}>Username</Text>
            <View style={ns.inputRow}>
              <Ionicons name="at-outline" size={20} color={colors.text.muted} />
              <TextInput style={ns.input} value={username} onChangeText={setUsername} placeholder="johndoe" placeholderTextColor={colors.text.muted} autoCapitalize="none" autoCorrect={false} />
            </View>
          </View>

          <View style={ns.inputGroup}>
            <Text style={ns.label}>Password</Text>
            <View style={ns.inputRow}>
              <Ionicons name="lock-closed-outline" size={20} color={colors.text.muted} />
              <TextInput style={ns.input} value={password} onChangeText={setPassword} placeholder="Min 8 characters" placeholderTextColor={colors.text.muted} secureTextEntry={!showPassword} />
              <TouchableOpacity onPress={() => setShowPassword(!showPassword)}>
                <Ionicons name={showPassword ? 'eye-off' : 'eye'} size={20} color={colors.text.muted} />
              </TouchableOpacity>
            </View>
            {password.length > 0 && (
              <View style={ns.strengthContainer}>
                <View style={ns.strengthBar}>
                  <View style={[ns.strengthFill, { width: `${(strength / 5) * 100}%`, backgroundColor: strengthColors[strength] || strengthColors[0] }]} />
                </View>
                <Text style={[ns.strengthText, { color: strengthColors[strength] || strengthColors[0] }]}>{strengthLabels[strength] || 'Very Weak'}</Text>
              </View>
            )}
          </View>

          <View style={ns.inputGroup}>
            <Text style={ns.label}>Confirm Password</Text>
            <View style={ns.inputRow}>
              <Ionicons name="lock-closed-outline" size={20} color={colors.text.muted} />
              <TextInput style={ns.input} value={confirmPassword} onChangeText={setConfirmPassword} placeholder="Repeat password" placeholderTextColor={colors.text.muted} secureTextEntry />
            </View>
          </View>

          <TouchableOpacity style={[presets.buttonPrimary, { marginTop: spacing.md }]} onPress={handleRegister} disabled={loading}>
            {loading ? <ActivityIndicator color="#FFF" /> : <Text style={ns.buttonText}>Create Account</Text>}
          </TouchableOpacity>

          <View style={ns.loginRow}>
            <Text style={ns.loginText}>Already have an account? </Text>
            <TouchableOpacity onPress={() => router.back()}>
              <Text style={ns.loginLink}>Sign In</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const ns = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  scrollContent: { paddingBottom: 40 },
  backButton: { paddingHorizontal: spacing.lg, paddingTop: 50 },
  header: { paddingHorizontal: spacing.xl, paddingBottom: spacing.lg },
  title: { fontSize: 28, fontWeight: '800', color: colors.text.primary, letterSpacing: -0.5 },
  subtitle: { fontSize: 16, color: colors.text.muted, marginTop: spacing.xs },
  form: { paddingHorizontal: spacing.xl },
  inputGroup: { marginBottom: spacing.lg },
  label: { fontSize: 14, fontWeight: '600', color: colors.text.secondary, marginBottom: spacing.sm },
  inputRow: { flexDirection: 'row', alignItems: 'center', backgroundColor: colors.bg.card, borderRadius: radius.md, paddingHorizontal: spacing.md, borderWidth: 1, borderColor: colors.surface.border, gap: spacing.sm },
  input: { flex: 1, height: 48, color: colors.text.primary, fontSize: 16 },
  strengthContainer: { flexDirection: 'row', alignItems: 'center', marginTop: spacing.xs, gap: spacing.sm },
  strengthBar: { flex: 1, height: 4, backgroundColor: colors.surface.divider, borderRadius: 2, overflow: 'hidden' },
  strengthFill: { height: '100%', borderRadius: 2 },
  strengthText: { fontSize: 12, fontWeight: '600' },
  buttonText: { fontSize: 16, fontWeight: '700', color: '#FFF' },
  loginRow: { flexDirection: 'row', justifyContent: 'center', marginTop: spacing.xl },
  loginText: { color: colors.text.muted, fontSize: 14 },
  loginLink: { color: colors.primary, fontSize: 14, fontWeight: '700' },
});
