/**
 * Privacy — consent per purpose, guardian status, account deletion and sign-out.
 * The root layout sends a user here while the server holds the account back
 * (no current consent, guardian not yet agreed, or deletion scheduled).
 */
import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, ScrollView, Switch, TouchableOpacity, TextInput, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, presets } from '../src/theme';
import { useUserStore } from '../src/stores';
import {
  ConsentState, PurposeId, DOCUMENTS, isBlocked, getConsent, setConsent, resendGuardianEmail,
  requestDeletion, cancelDeletion,
} from '../src/services/privacy';

export default function PrivacyScreen() {
  const router = useRouter();
  const clearUser = useUserStore((s) => s.clearUser);
  const [state, setState] = useState<ConsentState | null>(null);
  const [draft, setDraft] = useState<Partial<Record<PurposeId, boolean>>>({});
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [password, setPassword] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    const s = await getConsent();
    setState(s);
    if (s) setDraft(Object.fromEntries(Object.entries(s.purposes).map(([k, p]) => [k, !!p.granted])));
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const run = async (action: () => Promise<unknown>, done?: string) => {
    setBusy(true);
    try {
      await action();
      if (done) Alert.alert('Done', done);
      await load();
    } catch (e: any) {
      Alert.alert('Not saved', e?.message ?? String(e));
    }
    setBusy(false);
  };

  const signOut = async () => {
    await clearUser();
    router.replace('/login');
  };

  const saveConsent = () => run(async () => {
    const next = await setConsent(draft);
    if (!isBlocked(next)) router.replace('/(tabs)');
  });

  const confirmDeletion = () => {
    if (!password) {
      Alert.alert('Password needed', 'Enter your password to confirm.');
      return;
    }
    Alert.alert(
      'Delete account?',
      'Everything AdapFit holds about you will be erased in 30 minutes. Sign back in before then to cancel. Export your data first if you want a copy.',
      [
        { text: 'Keep account', style: 'cancel' },
        {
          text: 'Delete', style: 'destructive',
          onPress: () => run(async () => {
            await requestDeletion(password);
            await signOut();
          }),
        },
      ],
    );
  };

  if (loading) {
    return <View style={[ns.container, ns.center]}><ActivityIndicator color={colors.primary} /></View>;
  }
  if (!state) {
    return (
      <View style={[ns.container, ns.center]}>
        <Text style={ns.body}>Could not reach the server.</Text>
        <TouchableOpacity onPress={load}><Text style={ns.link}>Try again</Text></TouchableOpacity>
      </View>
    );
  }

  const due = state.deletion_due_at ? new Date(state.deletion_due_at * 1000) : null;
  const purposes = (Object.keys(state.purposes) as PurposeId[]).filter((id) => !(state.minor && id === 'analytics'));

  return (
    <ScrollView style={ns.container} contentContainerStyle={ns.content}>
      {!isBlocked(state) && (
        <TouchableOpacity onPress={() => router.back()} accessibilityLabel="Back">
          <Ionicons name="arrow-back" size={24} color={colors.text.primary} />
        </TouchableOpacity>
      )}
      <Text style={ns.title}>Privacy</Text>

      {due && (
        <View style={ns.notice}>
          <Text style={ns.noticeTitle}>Account deletion scheduled</Text>
          <Text style={ns.body}>Everything will be erased at {due.toLocaleTimeString()}.</Text>
          <TouchableOpacity style={[presets.buttonPrimary, ns.button]} disabled={busy}
            onPress={() => run(async () => { await cancelDeletion(); router.replace('/(tabs)'); })}>
            <Text style={ns.buttonText}>Keep my account</Text>
          </TouchableOpacity>
        </View>
      )}

      {state.guardian_pending && (
        <View style={ns.notice}>
          <Text style={ns.noticeTitle}>Waiting for your parent or guardian</Text>
          <Text style={ns.body}>
            We emailed them a link. Until they agree, the app cannot store anything for you. If nobody agrees within
            7 days the account is deleted.
          </Text>
          <TouchableOpacity disabled={busy} onPress={() => run(resendGuardianEmail, 'Email sent again.')}>
            <Text style={ns.link}>Send the email again</Text>
          </TouchableOpacity>
        </View>
      )}

      {state.guardian && (
        <Text style={ns.muted}>Consent given by {state.guardian.name} ({state.guardian.relationship}).</Text>
      )}

      {!state.guardian_pending && (
        <>
          <Text style={ns.section}>What you allow</Text>
          {state.needs_consent && (
            <Text style={ns.body}>Please review how AdapFit uses your data (policy {state.policy_version}).</Text>
          )}
          {purposes.map((id) => {
            const p = state.purposes[id];
            const childLocked = state.minor && !p.granted;
            return (
              <View key={id} style={ns.card}>
                <View style={{ flex: 1 }}>
                  <Text style={ns.cardTitle}>{p.title}{p.required ? ' (needed)' : ''}</Text>
                  <Text style={ns.muted}>{p.detail}</Text>
                  {childLocked && <Text style={ns.muted}>Only your parent or guardian can turn this on.</Text>}
                </View>
                <Switch
                  value={!!draft[id]}
                  disabled={childLocked}
                  onValueChange={(v) => setDraft((d) => ({ ...d, [id]: v }))}
                  trackColor={{ false: colors.surface.border, true: colors.primary }}
                  accessibilityLabel={p.title}
                />
              </View>
            );
          })}
          <TouchableOpacity style={[presets.buttonPrimary, ns.button]} disabled={busy} onPress={saveConsent}>
            <Text style={ns.buttonText}>{state.needs_consent ? 'Agree and continue' : 'Save choices'}</Text>
          </TouchableOpacity>
          {state.needs_consent && !draft.health_data && (
            <Text style={ns.muted}>The app cannot work without the first item. You can still export or delete your data.</Text>
          )}
        </>
      )}

      <Text style={ns.section}>Your data</Text>
      <TouchableOpacity style={ns.card} onPress={() => router.push('/(tabs)/data-export' as any)}>
        <Ionicons name="download-outline" size={20} color={colors.primary} />
        <Text style={[ns.cardTitle, ns.rowText]}>Export everything</Text>
      </TouchableOpacity>
      {DOCUMENTS.map((d) => (
        <TouchableOpacity key={d.id} style={ns.card} onPress={() => router.push({ pathname: '/legal', params: { doc: d.id } } as any)}>
          <Ionicons name="document-text-outline" size={20} color={colors.primary} />
          <Text style={[ns.cardTitle, ns.rowText]}>{d.title}</Text>
        </TouchableOpacity>
      ))}
      <TouchableOpacity style={ns.card} onPress={signOut}>
        <Ionicons name="log-out-outline" size={20} color={colors.text.secondary} />
        <Text style={[ns.cardTitle, ns.rowText]}>Sign out and clear this device</Text>
      </TouchableOpacity>

      {!due && (
        <>
          <Text style={ns.section}>Delete account</Text>
          {!deleting ? (
            <TouchableOpacity style={ns.card} onPress={() => setDeleting(true)}>
              <Ionicons name="trash-outline" size={20} color={colors.health.danger} />
              <Text style={[ns.cardTitle, ns.rowText, { color: colors.health.danger }]}>Delete my account and data</Text>
            </TouchableOpacity>
          ) : (
            <View style={ns.notice}>
              <Text style={ns.body}>Enter your password to confirm.</Text>
              <TextInput style={ns.input} value={password} onChangeText={setPassword} secureTextEntry
                placeholder="Password" placeholderTextColor={colors.text.muted} accessibilityLabel="Password" />
              <TouchableOpacity style={[ns.button, ns.danger]} disabled={busy} onPress={confirmDeletion}>
                <Text style={ns.buttonText}>Delete account</Text>
              </TouchableOpacity>
            </View>
          )}
        </>
      )}
    </ScrollView>
  );
}

const ns = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  center: { justifyContent: 'center', alignItems: 'center', padding: spacing.xl },
  content: { padding: spacing.lg, paddingTop: 56, paddingBottom: 80 },
  title: { fontSize: 28, fontWeight: '800', color: colors.text.primary, marginVertical: spacing.md },
  section: { fontSize: 13, fontWeight: '700', color: colors.text.muted, textTransform: 'uppercase', marginTop: spacing.xl, marginBottom: spacing.sm },
  body: { fontSize: 14, color: colors.text.secondary, lineHeight: 20, marginBottom: spacing.sm },
  muted: { fontSize: 12, color: colors.text.muted, marginTop: 4, lineHeight: 17 },
  link: { color: colors.primary, fontSize: 14, fontWeight: '600', marginTop: spacing.sm },
  notice: { backgroundColor: colors.bg.card, borderRadius: radius.md, padding: spacing.md, marginBottom: spacing.md, borderWidth: 1, borderColor: colors.surface.border },
  noticeTitle: { fontSize: 16, fontWeight: '700', color: colors.text.primary, marginBottom: spacing.xs },
  card: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, backgroundColor: colors.bg.card, borderRadius: radius.md, padding: spacing.md, marginBottom: spacing.sm },
  cardTitle: { fontSize: 15, fontWeight: '600', color: colors.text.primary },
  rowText: { flex: 1 },
  input: { height: 48, color: colors.text.primary, fontSize: 16, backgroundColor: colors.bg.deep, borderRadius: radius.md, paddingHorizontal: spacing.md, marginVertical: spacing.sm },
  button: { marginTop: spacing.md, alignItems: 'center', justifyContent: 'center', paddingVertical: 14, borderRadius: radius.md },
  danger: { backgroundColor: colors.health.danger },
  buttonText: { fontSize: 16, fontWeight: '700', color: '#FFF' },
});
