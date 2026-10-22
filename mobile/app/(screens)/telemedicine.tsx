/**
 * Telemedicine — where to consult a registered doctor online, which kind of
 * doctor to see, and a check against the NMC Indian Medical Register. AdapFit
 * does not host consultations; every service here opens outside the app.
 */
import React, { useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, TextInput, ActivityIndicator, Alert, Linking,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../../src/theme';
import { ScreenWrapper } from '../../src/components/ScreenWrapper';
import { GlassCard, SectionHeaderPremium } from '../../src/components/PremiumComponents';
import { useApis } from '../../src/hooks/useApi';
import { asArray, deleteJson, postJson } from '../../src/services/http';

interface Service { id: string; name: string; kind: string; description: string; cost: string; url: string; phone: string | null }
interface Guide { concern: string; see: string; when: string }
interface Match { name: string; registration_no: string; council: string; registration_date: string; qualification: string; removed: boolean }
interface Check { status: string; message: string; matches?: Match[]; register_url?: string }
interface Doctor { name: string; registration_no: string; council: string; specialty: string; verified_on_register: boolean }

const TINT = '#3B82F6';

export default function TelemedicineScreen() {
  const { data, loading, refreshing, refresh, reload } = useApis<{
    overview: { services: Service[]; specialty_guide: Guide[]; emergency: string; register_url: string; my_doctors: Doctor[] };
  }>({ overview: '/telemedicine/overview' });
  const o = data.overview;

  const [regNo, setRegNo] = useState('');
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);
  const [check, setCheck] = useState<Check | null>(null);

  const verify = async () => {
    if (!regNo.trim()) return;
    setBusy(true);
    setCheck(await postJson<Check>('/telemedicine/verify', { registration_no: regNo.trim(), name: name.trim() }));
    setBusy(false);
  };

  const save = async () => {
    if (name.trim().length < 2) {
      Alert.alert('Name needed', 'Enter the doctor\'s name to save them.');
      return;
    }
    setBusy(true);
    await postJson('/telemedicine/doctors', { registration_no: regNo.trim(), name: name.trim() });
    setBusy(false);
    setRegNo(''); setName(''); setCheck(null);
    await reload();
  };

  const remove = async (d: Doctor) => {
    await deleteJson(`/telemedicine/doctors/${encodeURIComponent(d.registration_no)}`);
    await reload();
  };

  return (
    <ScreenWrapper title="Telemedicine" subtitle="Consult a registered doctor online" gradient={[TINT, '#06B6D4']}
      loading={loading} refreshing={refreshing} onRefresh={refresh}>
      <GlassCard variant="light" style={styles.card}>
        <View style={styles.row}>
          <Ionicons name="warning" size={18} color="#DC2626" />
          <Text style={styles.muted}>{o?.emergency ?? 'For an emergency call 108 or 112.'}</Text>
        </View>
      </GlassCard>

      <SectionHeaderPremium icon="videocam" iconColor={TINT} title="Consult online" />
      {asArray<Service>(o?.services).map((s) => (
        <GlassCard key={s.id} variant="light" style={styles.card}>
          <Text style={styles.name}>{s.name} <Text style={styles.kind}>· {s.kind}</Text></Text>
          <Text style={styles.body}>{s.description}</Text>
          <Text style={styles.muted}>{s.cost}</Text>
          <View style={styles.row}>
            <TouchableOpacity style={styles.btn} onPress={() => Linking.openURL(s.url)} accessibilityRole="link">
              <Text style={styles.btnText}>Open {s.name}</Text>
            </TouchableOpacity>
            {!!s.phone && (
              <TouchableOpacity style={styles.btn} onPress={() => Linking.openURL(`tel:${s.phone}`)} accessibilityRole="button">
                <Text style={styles.btnText}>Call {s.phone}</Text>
              </TouchableOpacity>
            )}
          </View>
        </GlassCard>
      ))}

      <SectionHeaderPremium icon="git-branch" iconColor={TINT} title="Which doctor, how soon" />
      <GlassCard variant="light" style={styles.card}>
        {asArray<Guide>(o?.specialty_guide).map((g) => (
          <View key={g.concern} style={styles.item}>
            <Text style={styles.name}>{g.concern}</Text>
            <Text style={styles.body}>{g.see}</Text>
            <Text style={styles.muted}>{g.when}</Text>
          </View>
        ))}
      </GlassCard>

      <SectionHeaderPremium icon="shield-checkmark" iconColor={TINT} title="Check a doctor's registration" />
      <GlassCard variant="light" style={styles.card}>
        <Text style={styles.muted}>From the NMC Indian Medical Register. The number is on the prescription or the platform profile.</Text>
        <TextInput style={styles.input} value={regNo} onChangeText={setRegNo} placeholder="Registration number"
          placeholderTextColor={colors.text.muted} autoCapitalize="characters" maxLength={30} />
        <TextInput style={styles.input} value={name} onChangeText={setName} placeholder="Doctor's name (optional for check)"
          placeholderTextColor={colors.text.muted} maxLength={100} />
        <View style={styles.row}>
          <TouchableOpacity style={styles.btn} onPress={verify} disabled={busy} accessibilityRole="button">
            {busy ? <ActivityIndicator color="#fff" /> : <Text style={styles.btnText}>Check register</Text>}
          </TouchableOpacity>
          {check?.status === 'found' && (
            <TouchableOpacity style={styles.btn} onPress={save} disabled={busy} accessibilityRole="button">
              <Text style={styles.btnText}>Save doctor</Text>
            </TouchableOpacity>
          )}
        </View>
        {!!check && (
          <View style={styles.result}>
            <Text style={styles.body}>{check.message}</Text>
            {asArray<Match>(check.matches).map((m) => (
              <Text key={m.registration_no + m.council} style={[styles.muted, m.removed && { color: '#DC2626' }]}>
                {m.name} · {m.registration_no} · {m.council} · {m.qualification}{m.removed ? ' · REMOVED' : ''}
              </Text>
            ))}
            {!!check.register_url && (
              <Text style={styles.link} onPress={() => Linking.openURL(check.register_url!)}>Open the NMC register</Text>
            )}
          </View>
        )}
      </GlassCard>

      {asArray<Doctor>(o?.my_doctors).length > 0 && (
        <>
          <SectionHeaderPremium icon="people" iconColor={TINT} title="Your doctors" />
          {asArray<Doctor>(o?.my_doctors).map((d) => (
            <GlassCard key={d.registration_no} variant="light" style={styles.card}>
              <View style={styles.row}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.name}>{d.name}</Text>
                  <Text style={styles.muted}>{d.registration_no} · {d.council}</Text>
                  <Text style={[styles.muted, { color: d.verified_on_register ? '#16A34A' : '#F59E0B' }]}>
                    {d.verified_on_register ? 'Found on the register when saved' : 'Not found on the register'}
                  </Text>
                </View>
                <TouchableOpacity onPress={() => remove(d)} accessibilityLabel={`Remove ${d.name}`}>
                  <Ionicons name="trash-outline" size={20} color={colors.text.muted} />
                </TouchableOpacity>
              </View>
            </GlassCard>
          ))}
        </>
      )}
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  card: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.md },
  row: { flexDirection: 'row', gap: spacing.sm, alignItems: 'center', marginTop: spacing.sm },
  name: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  kind: { fontSize: 12, fontWeight: '400', color: colors.text.muted },
  body: { fontSize: 13, color: colors.text.secondary, marginTop: 4, lineHeight: 18 },
  muted: { flex: 1, fontSize: 12, color: colors.text.muted, marginTop: 2, lineHeight: 17 },
  item: { paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: colors.surface.border },
  input: { backgroundColor: colors.bg.input, borderRadius: radius.md, padding: 12, color: colors.text.primary, marginTop: spacing.sm },
  btn: { flex: 1, backgroundColor: TINT, borderRadius: radius.button, padding: 12, alignItems: 'center' },
  btnText: { color: '#FFF', fontWeight: '700', fontSize: 13 },
  result: { marginTop: spacing.md, padding: spacing.md, borderRadius: radius.md, borderWidth: 1, borderColor: colors.surface.border },
  link: { color: '#60A5FA', fontSize: 13, marginTop: 6 },
});
