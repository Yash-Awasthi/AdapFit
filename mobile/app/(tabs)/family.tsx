/**
 * Family — private connections with people you trust. Nothing is shared by
 * default; each person decides, per category, what the other may see, and can
 * pause or end the connection at any time.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, TextInput, Alert, Switch } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, spacing } from '../../src/theme';
import { GlassCard, SectionHeaderPremium } from '../../src/components/PremiumComponents';
import { asArray, getJson, postJson } from '../../src/services/http';

const TINT = '#EC4899';
const RELATIONS = ['parent', 'child', 'spouse', 'sibling', 'caregiver', 'custom'];
const SHAREABLE = [
  { key: 'view_emergency', label: 'Emergency medical info' },
  { key: 'view_recovery', label: 'Daily recovery score' },
  { key: 'view_sleep', label: 'Last night’s sleep' },
  { key: 'view_workouts', label: 'Workout count' },
];

export default function FamilyScreen() {
  const [invitee, setInvitee] = useState('');
  const [relation, setRelation] = useState('parent');
  const [invites, setInvites] = useState<any[]>([]);
  const [connections, setConnections] = useState<any[]>([]);
  const [open, setOpen] = useState<string | null>(null);
  const [member, setMember] = useState<Record<string, any>>({});

  const load = useCallback(async () => {
    const [i, c] = await Promise.all([getJson<any>('/family-network/invites'), getJson<any>('/family-network/connections')]);
    setInvites(asArray(i?.invites).filter((x: any) => !x.is_expired));
    setConnections(asArray(c?.connections));
  }, []);
  useEffect(() => { load(); }, [load]);

  const invite = async () => {
    if (!invitee.trim()) return;
    const r = await postJson<any>('/family-network/invite', { invitee: invitee.trim(), relationship: relation });
    if (r?.message) Alert.alert('Invite sent', r.message);
    setInvitee('');
  };
  const accept = async (id: string) => { await postJson('/family-network/invite/accept', { invite_id: id }); load(); };
  const decline = async (id: string) => { await postJson(`/family-network/invite/decline?invite_id=${id}`); load(); };
  const toggle = async (conn: any, key: string, value: boolean) => {
    await postJson('/family-network/permissions', { connection_id: conn.connection_id, permissions: { ...conn.i_share, [key]: value } });
    load();
  };
  const view = async (id: string) => {
    setOpen(open === id ? null : id);
    if (open !== id) setMember({ ...member, [id]: await getJson(`/family-network/member/${id}`) });
  };
  const end = (id: string) => Alert.alert('End this connection?', 'Sharing stops for both of you. This cannot be undone.', [
    { text: 'Cancel', style: 'cancel' },
    { text: 'End', style: 'destructive', onPress: async () => { await postJson(`/family-network/connection/revoke?connection_id=${id}`); load(); } },
  ]);

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={{ paddingBottom: 100 }}>
        <LinearGradient colors={[TINT, '#BE185D', colors.bg.deep]} style={styles.hero}>
          <Text style={styles.heroMuted}>Family</Text>
          <Text style={styles.heroTitle}>{connections.length ? `${connections.length} connected` : 'Look after each other'}</Text>
          <Text style={styles.heroMuted}>Nothing is shared until you switch it on.</Text>
        </LinearGradient>

        {invites.length > 0 && (
          <View style={styles.section}>
            <SectionHeaderPremium title="Invites for You" icon="mail" iconColor={TINT} />
            {invites.map((i) => (
              <GlassCard key={i.invite_id} style={styles.gap}>
                <Text style={styles.title}>Someone added you as their {i.relationship}</Text>
                {i.message ? <Text style={styles.sub}>“{i.message}”</Text> : null}
                <View style={styles.row}>
                  <TouchableOpacity style={[styles.btn, { flex: 1 }]} onPress={() => accept(i.invite_id)}><Text style={styles.btnText}>Accept</Text></TouchableOpacity>
                  <TouchableOpacity style={[styles.btn, styles.ghost, { flex: 1 }]} onPress={() => decline(i.invite_id)}><Text style={[styles.btnText, { color: TINT }]}>Decline</Text></TouchableOpacity>
                </View>
              </GlassCard>
            ))}
          </View>
        )}

        <View style={styles.section}>
          <SectionHeaderPremium title="Connections" icon="people" iconColor={TINT} />
          {connections.length === 0 && <Text style={styles.sub}>No one yet. Invite a family member below.</Text>}
          {connections.map((c) => {
            const m = member[c.connection_id];
            return (
              <GlassCard key={c.connection_id} style={styles.gap}>
                <TouchableOpacity onPress={() => view(c.connection_id)}>
                  <Text style={styles.title}>Your {c.relationship} · since {c.connected_since}</Text>
                  <Text style={styles.sub}>Tap to see what they share with you</Text>
                </TouchableOpacity>
                {open === c.connection_id && m && (
                  <View style={styles.box}>
                    {m.shared?.length === 0 && <Text style={styles.sub}>They have not shared anything yet.</Text>}
                    {m.recovery && <Text style={styles.body}>Recovery {m.recovery.recovery_score ?? '--'} ({m.recovery.readiness_state ?? 'no check-in'}) on {m.recovery.log_date}</Text>}
                    {m.sleep && <Text style={styles.body}>Last night: {m.sleep.total_sleep_hours ?? '--'} h sleep</Text>}
                    {m.workouts_last_7_days !== undefined && <Text style={styles.body}>{m.workouts_last_7_days} workouts this week</Text>}
                    {m.emergency && (
                      <Text style={styles.body}>Blood type {m.emergency.blood_type ?? '--'} · allergies {asArray<string>(m.emergency.allergies).join(', ') || 'none recorded'}</Text>
                    )}
                  </View>
                )}
                <Text style={[styles.label, { marginTop: 12 }]}>What you share with them</Text>
                {SHAREABLE.map((p) => (
                  <View key={p.key} style={styles.toggle}>
                    <Text style={styles.body}>{p.label}</Text>
                    <Switch value={!!c.i_share?.[p.key]} onValueChange={(v) => toggle(c, p.key, v)} trackColor={{ true: TINT }} />
                  </View>
                ))}
                <Text style={styles.link} onPress={() => end(c.connection_id)}>End connection</Text>
              </GlassCard>
            );
          })}
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Invite Someone" icon="person-add" iconColor={TINT} />
          <GlassCard>
            <TextInput style={styles.input} value={invitee} onChangeText={setInvitee} autoCapitalize="none"
              placeholder="Their email or username on AdapFit" placeholderTextColor={colors.text.muted} />
            <View style={styles.chips}>
              {RELATIONS.map((r) => (
                <TouchableOpacity key={r} style={[styles.chip, relation === r && styles.chipOn]} onPress={() => setRelation(r)}>
                  <Text style={[styles.chipText, relation === r && { color: TINT, fontWeight: '700' }]}>{r}</Text>
                </TouchableOpacity>
              ))}
            </View>
            <TouchableOpacity style={styles.btn} onPress={invite}><Text style={styles.btnText}>Send invite</Text></TouchableOpacity>
          </GlassCard>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  hero: { paddingTop: 60, paddingBottom: 24, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 24, borderBottomRightRadius: 24 },
  heroMuted: { color: 'rgba(255,255,255,0.8)', fontSize: 13, marginTop: 4 },
  heroTitle: { color: '#fff', fontSize: 26, fontWeight: '800', marginTop: 6 },
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  gap: { marginBottom: 10 },
  title: { color: colors.text.primary, fontSize: 15, fontWeight: '700', textTransform: 'capitalize' },
  sub: { color: colors.text.muted, fontSize: 12, marginTop: 3 },
  body: { color: colors.text.secondary, fontSize: 14, marginTop: 4, flex: 1 },
  label: { color: colors.text.secondary, fontSize: 13, fontWeight: '600' },
  box: { borderWidth: 1, borderColor: colors.surface.border, borderRadius: 10, padding: 10, marginTop: 10 },
  toggle: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 6 },
  input: { backgroundColor: colors.bg.card, borderRadius: 12, padding: 12, color: colors.text.primary, borderWidth: 1, borderColor: colors.surface.border },
  btn: { backgroundColor: TINT, borderRadius: 12, padding: 12, alignItems: 'center', marginTop: 10 },
  ghost: { backgroundColor: 'transparent', borderWidth: 1, borderColor: TINT },
  btnText: { color: '#fff', fontWeight: '700' },
  row: { flexDirection: 'row', gap: 8 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 10 },
  chip: { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 20, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border },
  chipOn: { backgroundColor: TINT + '25', borderColor: TINT },
  chipText: { color: colors.text.muted, fontSize: 12, textTransform: 'capitalize' },
  link: { color: '#F87171', fontSize: 13, marginTop: 12 },
});
