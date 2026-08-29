/**
 * Login Screen — Premium auth UI with gradient header
 */
import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, KeyboardAvoidingView, Platform, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, radius, presets } from '../src/theme';

import { API_V1 as API } from '../src/services/config';
import { setToken } from '../src/services/authToken';
import { useUserStore } from '../src/stores';

export default function LoginScreen() {
  const router = useRouter();
  const setUser = useUserStore((s) => s.setUser);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) {
      Alert.alert('Error', 'Please enter email and password');
      return;
    }
    setLoading(true);
    try {
      const r = await fetch(`${API}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), password }),
      });
      const data = await r.json();
      if (r.ok && data.tokens) {
        await setToken(data.tokens.access_token ?? null);
        // The root layout redirects to onboarding whenever the store holds no
        // profile, so the signed-in user has to be recorded before navigating.
        if (data.user?.id) {
          await setUser({
            id: data.user.id,
            email: data.user.email,
            name: data.user.display_name ?? data.user.username ?? null,
          });
        }
        router.replace('/(tabs)');
      } else {
        Alert.alert('Login Failed', data.detail || 'Invalid credentials');
      }
    } catch {
      Alert.alert('Error', 'Network error. Please try again.');
    }
    setLoading(false);
  };

  return (
    <KeyboardAvoidingView style={ns.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <View style={ns.header}>
        <View style={ns.logoContainer}>
          <Ionicons name="fitness" size={48} color="#FFF" />
        </View>
        <Text style={ns.title}>AdapFit</Text>
        <Text style={ns.subtitle}>Your AI-Powered Health Platform</Text>
      </View>

      <View style={ns.form}>
        <View style={ns.inputGroup}>
          <Text style={ns.label}>Email</Text>
          <View style={ns.inputRow}>
            <Ionicons name="mail-outline" size={20} color={colors.text.muted} />
            <TextInput
              style={ns.input}
              value={email}
              onChangeText={setEmail}
              placeholder="you@example.com"
              placeholderTextColor={colors.text.muted}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
            />
          </View>
        </View>

        <View style={ns.inputGroup}>
          <Text style={ns.label}>Password</Text>
          <View style={ns.inputRow}>
            <Ionicons name="lock-closed-outline" size={20} color={colors.text.muted} />
            <TextInput
              style={ns.input}
              value={password}
              onChangeText={setPassword}
              placeholder="Enter your password"
              placeholderTextColor={colors.text.muted}
              secureTextEntry={!showPassword}
            />
            <TouchableOpacity onPress={() => setShowPassword(!showPassword)}>
              <Ionicons name={showPassword ? 'eye-off' : 'eye'} size={20} color={colors.text.muted} />
            </TouchableOpacity>
          </View>
        </View>

        <TouchableOpacity style={[presets.buttonPrimary, { marginTop: spacing.md }]} onPress={handleLogin} disabled={loading}>
          {loading ? <ActivityIndicator color="#FFF" /> : <Text style={ns.buttonText}>Sign In</Text>}
        </TouchableOpacity>

        <TouchableOpacity style={ns.forgotPassword}>
          <Text style={ns.forgotText}>Forgot Password?</Text>
        </TouchableOpacity>

        <View style={ns.divider}>
          <View style={ns.dividerLine} />
          <Text style={ns.dividerText}>or</Text>
          <View style={ns.dividerLine} />
        </View>

        <TouchableOpacity style={[presets.buttonSecondary, { marginTop: spacing.md }]} onPress={() => router.push('/register' as any)}>
          <Text style={[ns.buttonText, { color: colors.primary }]}>Create Account</Text>
        </TouchableOpacity>
      </View>

      <Text style={ns.footer}>By signing in, you agree to our Terms of Service and Privacy Policy</Text>
    </KeyboardAvoidingView>
  );
}

const ns = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  header: { alignItems: 'center', paddingTop: 80, paddingBottom: spacing.xl },
  logoContainer: { width: 80, height: 80, borderRadius: 40, backgroundColor: colors.primary, justifyContent: 'center', alignItems: 'center', marginBottom: spacing.md },
  title: { fontSize: 32, fontWeight: '800', color: colors.text.primary, letterSpacing: -0.5 },
  subtitle: { fontSize: 16, color: colors.text.muted, marginTop: spacing.xs },
  form: { flex: 1, paddingHorizontal: spacing.xl, paddingTop: spacing.lg },
  inputGroup: { marginBottom: spacing.lg },
  label: { fontSize: 14, fontWeight: '600', color: colors.text.secondary, marginBottom: spacing.sm },
  inputRow: { flexDirection: 'row', alignItems: 'center', backgroundColor: colors.bg.card, borderRadius: radius.md, paddingHorizontal: spacing.md, borderWidth: 1, borderColor: colors.surface.border, gap: spacing.sm },
  input: { flex: 1, height: 48, color: colors.text.primary, fontSize: 16 },
  buttonText: { fontSize: 16, fontWeight: '700', color: '#FFF' },
  forgotPassword: { alignItems: 'center', marginTop: spacing.md },
  forgotText: { color: colors.primary, fontSize: 14 },
  divider: { flexDirection: 'row', alignItems: 'center', marginVertical: spacing.lg },
  dividerLine: { flex: 1, height: 1, backgroundColor: colors.surface.border },
  dividerText: { marginHorizontal: spacing.md, color: colors.text.muted, fontSize: 14 },
  footer: { textAlign: 'center', color: colors.text.muted, fontSize: 12, padding: spacing.lg, paddingBottom: 40 },
});
