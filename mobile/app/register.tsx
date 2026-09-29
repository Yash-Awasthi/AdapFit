/**
 * Register Screen — Premium signup UI
 */
import React, { useEffect, useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, KeyboardAvoidingView, Platform, ActivityIndicator, ScrollView, Switch } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, radius, presets } from '../src/theme';

import { API_V1 as API } from '../src/services/config';
import { setTokens } from '../src/services/authToken';
import { useUserStore } from '../src/stores';
import { DOCUMENTS, Purpose, PurposeId, getPurposes } from '../src/services/privacy';

function ageFrom(birth: string): number | null {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(birth)) return null;
  const b = new Date(`${birth}T00:00:00`);
  if (isNaN(b.getTime())) return null;
  const now = new Date();
  let age = now.getFullYear() - b.getFullYear();
  if (now.getMonth() < b.getMonth() || (now.getMonth() === b.getMonth() && now.getDate() < b.getDate())) age--;
  return age;
}

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
  const [birthDate, setBirthDate] = useState('');
  const [guardianEmail, setGuardianEmail] = useState('');
  const [purposes, setPurposes] = useState<Record<PurposeId, Purpose> | null>(null);
  const [adultAge, setAdultAge] = useState(18);
  const [choices, setChoices] = useState<Record<PurposeId, boolean>>({ health_data: false, ai: false, sharing: false, analytics: false });

  useEffect(() => {
    getPurposes().then((p) => {
      if (p) {
        setPurposes(p.purposes);
        setAdultAge(p.adult_age);
      }
    });
  }, []);

  const age = ageFrom(birthDate);
  const minor = age !== null && age < adultAge;

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
    if (age === null || age < 0 || age > 120) {
      Alert.alert('Date of birth', 'Enter your date of birth as YYYY-MM-DD');
      return;
    }
    if (minor && !guardianEmail.includes('@')) {
      Alert.alert('Parent or guardian', "Under 18, enter a parent or guardian's email so they can agree for you.");
      return;
    }
    if (!minor && !choices.health_data) {
      Alert.alert('Consent needed', 'AdapFit cannot work without storing your health data. Turn on the first item to continue.');
      return;
    }
    setLoading(true);
    try {
      const r = await fetch(`${API}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(), username: username.trim(), password, display_name: displayName.trim(),
          birth_date: birthDate, guardian_email: minor ? guardianEmail.trim() : '',
          consent: minor ? { ...choices, analytics: false } : choices,
        }),
      });
      const data = await r.json();
      if (r.ok && data.tokens) {
        await setTokens(data.tokens);
        if (data.user?.id) {
          await setUser({
            id: data.user.id,
            email: data.user.email,
            name: data.user.display_name ?? data.user.username ?? null,
          });
        }
        router.replace(data.privacy?.guardian_pending ? ('/privacy' as any) : '/(tabs)');
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

  // Score runs 0-5 while the labels run 0-4; 5 of 5 is "Very Strong", not an out-of-range fallback.
  const strength = Math.max(0, passwordStrength(password) - 1);
  const strengthColors = ['#EF4444', '#F97316', '#EAB308', '#22C55E', '#10B981'];
  const strengthLabels = ['Very Weak', 'Weak', 'Fair', 'Strong', 'Very Strong'];

  return (
    <KeyboardAvoidingView style={ns.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={ns.scrollContent} showsVerticalScrollIndicator={false}>
        <TouchableOpacity accessibilityRole="button" accessibilityLabel="Back" style={ns.backButton} onPress={() => router.back()}>
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
              <TouchableOpacity accessibilityRole="button" accessibilityLabel={showPassword ? 'Hide password' : 'Show password'} onPress={() => setShowPassword(!showPassword)}>
                <Ionicons name={showPassword ? 'eye-off' : 'eye'} size={20} color={colors.text.muted} />
              </TouchableOpacity>
            </View>
            {password.length > 0 && (
              <View style={ns.strengthContainer}>
                <View style={ns.strengthBar}>
                  <View style={[ns.strengthFill, { width: `${((strength + 1) / 5) * 100}%`, backgroundColor: strengthColors[strength] || strengthColors[0] }]} />
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

          <View style={ns.inputGroup}>
            <Text style={ns.label}>Date of Birth</Text>
            <View style={ns.inputRow}>
              <Ionicons name="calendar-outline" size={20} color={colors.text.muted} />
              <TextInput style={ns.input} value={birthDate} onChangeText={setBirthDate} placeholder="YYYY-MM-DD" placeholderTextColor={colors.text.muted} keyboardType="numbers-and-punctuation" maxLength={10} accessibilityLabel="Date of birth, year month day" />
            </View>
          </View>

          {!!minor && (
            <View style={ns.inputGroup}>
              <Text style={ns.label}>Parent or Guardian's Email</Text>
              <Text style={ns.hint}>Under {adultAge}, a parent or guardian has to agree before the app stores anything for you. We will email them.</Text>
              <View style={ns.inputRow}>
                <Ionicons name="people-outline" size={20} color={colors.text.muted} />
                <TextInput style={ns.input} value={guardianEmail} onChangeText={setGuardianEmail} placeholder="parent@example.com" placeholderTextColor={colors.text.muted} keyboardType="email-address" autoCapitalize="none" />
              </View>
            </View>
          )}

          {!!purposes && (
            <View style={ns.inputGroup}>
              <Text style={ns.label}>{minor ? 'What you would like (your guardian decides)' : 'What you allow'}</Text>
              {(Object.keys(purposes) as PurposeId[]).filter((id) => !(minor && id === 'analytics')).map((id) => (
                <View key={id} style={ns.consentRow}>
                  <View style={{ flex: 1 }}>
                    <Text style={ns.consentTitle}>{purposes[id].title}{purposes[id].required ? ' (needed)' : ''}</Text>
                    <Text style={ns.hint}>{purposes[id].detail}</Text>
                  </View>
                  <Switch value={choices[id]} onValueChange={(v) => setChoices((c) => ({ ...c, [id]: v }))}
                    trackColor={{ false: colors.surface.border, true: colors.primary }} accessibilityLabel={purposes[id].title} />
                </View>
              ))}
              <Text style={ns.hint}>You can change these any time in Settings, Privacy.</Text>
            </View>
          )}

          <View style={ns.docsRow}>
            {DOCUMENTS.map((d) => (
              <TouchableOpacity key={d.id} onPress={() => router.push({ pathname: '/legal', params: { doc: d.id } } as any)}>
                <Text style={ns.loginLink}>{d.title}</Text>
              </TouchableOpacity>
            ))}
          </View>
          <Text style={ns.hint}>By creating an account you accept the Terms of Service and Health Disclaimer.</Text>

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
  hint: { fontSize: 12, color: colors.text.muted, marginTop: 4, marginBottom: spacing.xs, lineHeight: 17 },
  consentRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, backgroundColor: colors.bg.card, borderRadius: radius.md, padding: spacing.md, marginBottom: spacing.sm },
  consentTitle: { fontSize: 14, fontWeight: '600', color: colors.text.primary },
  docsRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md, marginBottom: spacing.xs },
});
