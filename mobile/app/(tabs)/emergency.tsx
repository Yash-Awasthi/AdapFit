/**
 * Emergency — SOS, contacts and the medical card.
 *
 * The SOS button used to be a local toggle that said "sharing location with
 * contacts" while doing nothing. It now activates a real alert, asks first
 * because activating notifies people, and offers to cancel — a screen someone
 * reaches in trouble must not claim help is coming when it is not.
 *
 * Contacts and medical details are this user's own, and nothing is shown
 * unless it was entered: an invented blood type on an emergency card is the
 * worst possible placeholder.
 */
import React, { useCallback, useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, Alert, Linking, TextInput, Modal,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { colors, spacing, radius } from '../../src/theme';
import { ScreenWrapper } from '../../src/components/ScreenWrapper';
import { GlassCard, SectionHeaderPremium } from '../../src/components/PremiumComponents';
import { Pulse } from '../../src/components/AnimationSystem';
import { useApis } from '../../src/hooks/useApi';
import { postJson, asArray } from '../../src/services/http';

interface Contact {
  id: string;
  name: string;
  phone: string;
  relationship: string;
  is_primary: boolean;
}

interface MedicalInfo {
  blood_type: string;
  allergies: string[];
  conditions: string[];
  medications: string[];
  emergency_note: string;
}

interface ActiveAlert {
  alert_id: string;
  contacts_notified: string[];
  location_shared: boolean;
  message: string;
}

const RELATIONSHIP_COLOR: Record<string, string> = {
  doctor: '#3B82F6',
  family: '#EC4899',
  friend: '#F97316',
  partner: '#EC4899',
};

function colorFor(relationship: string): string {
  return RELATIONSHIP_COLOR[relationship?.toLowerCase()] ?? '#22C55E';
}

function AddContactModal({ visible, onClose, onAdded }: {
  visible: boolean; onClose: () => void; onAdded: () => void;
}) {
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [relationship, setRelationship] = useState('family');
  const [saving, setSaving] = useState(false);

  const save = async () => {
    if (!name.trim() || !phone.trim()) {
      Alert.alert('Add contact', 'A name and phone number are both needed.');
      return;
    }
    setSaving(true);
    const result = await postJson('/emergency/contact', {
      name: name.trim(),
      phone: phone.trim(),
      relationship: relationship.trim() || 'family',
      is_primary: false,
    });
    setSaving(false);
    if (!result) {
      Alert.alert('Not saved', 'The contact could not be saved.');
      return;
    }
    setName('');
    setPhone('');
    onAdded();
    onClose();
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.modalBackdrop}>
        <View style={styles.modalCard}>
          <Text style={styles.modalTitle}>Add an emergency contact</Text>
          <TextInput style={styles.input} placeholder="Name" placeholderTextColor={colors.text.muted}
            value={name} onChangeText={setName} accessibilityLabel="Contact name" />
          <TextInput style={styles.input} placeholder="Phone number" placeholderTextColor={colors.text.muted}
            value={phone} onChangeText={setPhone} keyboardType="phone-pad" accessibilityLabel="Phone number" />
          <TextInput style={styles.input} placeholder="Relationship (family, doctor, friend)"
            placeholderTextColor={colors.text.muted} value={relationship} onChangeText={setRelationship}
            accessibilityLabel="Relationship" />
          <View style={styles.modalActions}>
            <TouchableOpacity onPress={onClose} style={[styles.modalButton, styles.modalCancel]}>
              <Text style={styles.modalCancelText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={save} disabled={saving} style={[styles.modalButton, styles.modalSave]}>
              <Text style={styles.modalSaveText}>{saving ? 'Saving…' : 'Add'}</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const BLOOD_TYPES = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'unknown'];

function MedicalInfoEditor({ initial, onSaved }: { initial: MedicalInfo | null; onSaved: () => void }) {
  const [blood, setBlood] = useState(initial?.blood_type ?? 'unknown');
  const [allergies, setAllergies] = useState((initial?.allergies ?? []).join(', '));
  const [conditions, setConditions] = useState((initial?.conditions ?? []).join(', '));
  const [medications, setMedications] = useState((initial?.medications ?? []).join(', '));
  const [note, setNote] = useState(initial?.emergency_note ?? '');
  const list = (t: string) => t.split(',').map((x) => x.trim()).filter(Boolean);
  const save = async () => {
    const r = await postJson('/emergency/medical-info', {
      blood_type: blood, allergies: list(allergies), conditions: list(conditions), medications: list(medications), emergency_note: note,
    });
    if (!r) return Alert.alert('Not saved', 'Your medical info could not be saved.');
    onSaved();
  };
  return (
    <View>
      <Text style={styles.medicalLabel}>Blood type</Text>
      <View style={styles.tagRow}>
        {BLOOD_TYPES.map((b) => (
          <TouchableOpacity key={b} onPress={() => setBlood(b)}
            style={[styles.medicalTag, { backgroundColor: blood === b ? '#EF444430' : colors.bg.card }]}>
            <Text style={[styles.medicalTagText, { color: blood === b ? '#EF4444' : colors.text.muted }]}>{b}</Text>
          </TouchableOpacity>
        ))}
      </View>
      {[['Allergies (comma separated)', allergies, setAllergies], ['Conditions', conditions, setConditions],
        ['Medications and doses', medications, setMedications], ['Note for responders', note, setNote]].map(([label, v, set]: any) => (
        <View key={label} style={{ marginTop: 10 }}>
          <Text style={styles.medicalLabel}>{label}</Text>
          <TextInput style={styles.editInput} value={v} onChangeText={set} multiline placeholderTextColor={colors.text.muted} />
        </View>
      ))}
      <TouchableOpacity style={styles.saveBtn} onPress={save}><Text style={styles.saveBtnText}>Save medical info</Text></TouchableOpacity>
    </View>
  );
}

export default function EmergencyScreen() {
  const [editing, setEditing] = useState(false);
  const [alert_, setAlert] = useState<ActiveAlert | null>(null);
  const [busy, setBusy] = useState(false);
  const [adding, setAdding] = useState(false);

  const { data, loading, refreshing, refresh, reload } = useApis<{
    contacts: { contacts: Contact[] };
    medical: MedicalInfo;
  }>({
    contacts: '/emergency/contacts',
    medical: '/emergency/medical-info',
  });

  const contacts = asArray<Contact>(data.contacts?.contacts);
  const medical = data.medical ?? null;

  const activate = useCallback(async () => {
    setBusy(true);
    // Location is sent when the app has it; the alert goes out either way
    // rather than being blocked on a permission prompt in an emergency.
    const result = await postJson<ActiveAlert & { error?: string }>('/emergency/activate', {});
    setBusy(false);
    if (!result || result.error) {
      Alert.alert(
        'SOS not sent',
        result?.error ?? 'The alert could not be sent. Call your local emergency number directly.'
      );
      return;
    }
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
    setAlert(result);
  }, []);

  const confirmActivate = () => {
    if (contacts.length === 0) {
      Alert.alert(
        'No contacts yet',
        'Add at least one emergency contact so there is somebody to notify. In an emergency now, call your local emergency number directly.'
      );
      return;
    }
    Alert.alert(
      'Send emergency alert?',
      `This notifies ${contacts.length} contact${contacts.length === 1 ? '' : 's'} and shares your medical details with them.`,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Send alert', style: 'destructive', onPress: activate },
      ]
    );
  };

  const cancel = useCallback(async () => {
    if (!alert_) return;
    setBusy(true);
    await postJson(`/emergency/cancel/${alert_.alert_id}`, {});
    setBusy(false);
    setAlert(null);
  }, [alert_]);

  const call = (phone: string) => Linking.openURL(`tel:${phone.replace(/[^\d+]/g, '')}`);

  const hasMedical = medical && (
    (medical.blood_type && medical.blood_type !== 'unknown') ||
    medical.allergies?.length || medical.conditions?.length || medical.medications?.length
  );

  return (
    <ScreenWrapper
      title="Emergency"
      subtitle="Quick access to emergency services"
      gradient={['#EF4444', '#F97316']}
      loading={loading}
      refreshing={refreshing}
      onRefresh={refresh}
    >
      <View style={styles.sosSection}>
        <View style={styles.sosContainer}>
          <Pulse color="#EF4444" size={140}>
            <TouchableOpacity
              style={[styles.sosButton, alert_ && styles.sosButtonActive]}
              onPress={alert_ ? cancel : confirmActivate}
              disabled={busy}
              accessibilityRole="button"
              accessibilityLabel={alert_ ? 'Cancel the active emergency alert' : 'Send an emergency alert'}
            >
              <Ionicons name={alert_ ? 'close' : 'call'} size={36} color="#FFF" />
              <Text style={styles.sosLabel}>{alert_ ? 'CANCEL' : 'SOS'}</Text>
            </TouchableOpacity>
          </Pulse>
        </View>
        <Text style={styles.sosHint}>
          {alert_ ? 'Tap again to cancel this alert' : 'Tap to alert your emergency contacts'}
        </Text>
        {!!alert_ && (
          <View style={styles.sosActiveBanner}>
            <Ionicons name="warning" size={16} color="#EF4444" />
            <Text style={styles.sosActiveText}>
              {alert_.contacts_notified.length > 0
                ? `Alert sent to ${alert_.contacts_notified.join(', ')}.`
                : 'Alert raised, but no contacts were notified.'}
              {alert_.location_shared ? ' Location shared.' : ' Location was not shared.'}
            </Text>
          </View>
        )}
        <TouchableOpacity
          style={styles.emergencyServicesRow}
          onPress={() => call('112')}
          accessibilityRole="button"
          accessibilityLabel="Call emergency services"
        >
          <Ionicons name="call" size={16} color="#EF4444" />
          <Text style={styles.emergencyServicesText}>
            In a real emergency, call your local emergency number
          </Text>
        </TouchableOpacity>
      </View>

      <SectionHeaderPremium
        icon="people"
        iconColor="#EF4444"
        title="Emergency Contacts"
        action={{ label: 'Add', onPress: () => setAdding(true) }}
      />
      {contacts.length === 0 ? (
        <GlassCard variant="light" style={styles.contactCard}>
          <Text style={styles.emptyTitle}>No contacts yet</Text>
          <Text style={styles.emptyText}>
            Add the people who should be told if you raise an alert. Nobody is notified until
            you do.
          </Text>
        </GlassCard>
      ) : (
        contacts.map((contact) => {
          const tint = colorFor(contact.relationship);
          return (
            <GlassCard key={contact.id} variant="light" style={styles.contactCard}>
              <View style={styles.contactRow}>
                <View style={[styles.contactIcon, { backgroundColor: tint + '15' }]}>
                  <Ionicons name={contact.is_primary ? 'star' : 'person'} size={20} color={tint} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.contactName}>{contact.name}</Text>
                  <Text style={styles.contactPhone}>
                    {contact.phone} · {contact.relationship}{contact.is_primary ? ' · primary' : ''}
                  </Text>
                </View>
                <TouchableOpacity
                  style={[styles.callBtn, { backgroundColor: '#22C55E15' }]}
                  onPress={() => call(contact.phone)}
                  accessibilityRole="button"
                  accessibilityLabel={`Call ${contact.name}`}
                >
                  <Ionicons name="call" size={18} color="#22C55E" />
                </TouchableOpacity>
              </View>
            </GlassCard>
          );
        })
      )}

      <SectionHeaderPremium icon="medical" iconColor="#3B82F6" title="Medical Info"
        action={{ label: editing ? 'Cancel' : 'Edit', onPress: () => setEditing(!editing) }} />
      <GlassCard variant="light" style={styles.medicalCard}>
        {editing ? (
          <MedicalInfoEditor initial={medical} onSaved={() => { setEditing(false); reload(); }} />
        ) : !hasMedical ? (
          <Text style={styles.emptyText}>
            Nothing recorded. Blood type, allergies and current medications are what a
            responder needs first. Tap Edit to add them.
          </Text>
        ) : (
          <>
            <View style={styles.medicalRow}>
              <Text style={styles.medicalLabel}>Blood Type</Text>
              <Text style={[styles.medicalValue, { color: '#EF4444' }]}>
                {medical!.blood_type && medical!.blood_type !== 'unknown' ? medical!.blood_type : 'Not recorded'}
              </Text>
            </View>
            {[
              { label: 'Allergies', items: medical!.allergies, color: '#EF4444' },
              { label: 'Conditions', items: medical!.conditions, color: '#F59E0B' },
              { label: 'Medications', items: medical!.medications, color: '#3B82F6' },
            ].map((group) => (
              <View key={group.label} style={styles.medicalRow}>
                <Text style={styles.medicalLabel}>{group.label}</Text>
                {group.items?.length ? (
                  <View style={styles.tagRow}>
                    {group.items.map((item, i) => (
                      <View key={i} style={[styles.medicalTag, { backgroundColor: group.color + '15' }]}>
                        <Text style={[styles.medicalTagText, { color: group.color }]}>{item}</Text>
                      </View>
                    ))}
                  </View>
                ) : (
                  <Text style={styles.medicalValue}>None recorded</Text>
                )}
              </View>
            ))}
            {medical!.emergency_note ? (
              <Text style={styles.medicalNote}>{medical!.emergency_note}</Text>
            ) : null}
          </>
        )}
      </GlassCard>

      <AddContactModal visible={adding} onClose={() => setAdding(false)} onAdded={reload} />
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  editInput: { backgroundColor: colors.bg.card, borderRadius: 10, padding: 10, color: colors.text.primary, marginTop: 4 },
  saveBtn: { backgroundColor: '#3B82F6', borderRadius: 12, padding: 13, alignItems: 'center', marginTop: 14 },
  saveBtnText: { color: '#fff', fontWeight: '700' },
  sosSection: { alignItems: 'center', paddingVertical: spacing.xl, paddingHorizontal: spacing.screenPadding },
  sosContainer: { marginBottom: spacing.md },
  sosButton: { width: 100, height: 100, borderRadius: 50, backgroundColor: '#EF4444', justifyContent: 'center', alignItems: 'center' },
  sosButtonActive: { backgroundColor: '#DC2626' },
  sosLabel: { fontSize: 16, fontWeight: '800', color: '#FFF', marginTop: 4 },
  sosHint: { fontSize: 13, color: colors.text.muted, marginTop: spacing.sm, textAlign: 'center' },
  sosActiveBanner: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginTop: spacing.md, paddingHorizontal: spacing.lg, paddingVertical: spacing.md, backgroundColor: '#EF444415', borderRadius: radius.md, borderWidth: 1, borderColor: '#EF444430' },
  sosActiveText: { fontSize: 12, color: '#EF4444', fontWeight: '600', flex: 1, lineHeight: 17 },
  emergencyServicesRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs, marginTop: spacing.lg },
  emergencyServicesText: { fontSize: 12, color: colors.text.muted },

  contactCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  contactRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  contactIcon: { width: 44, height: 44, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  contactName: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  contactPhone: { fontSize: 13, color: colors.text.muted, marginTop: 2 },
  callBtn: { width: 40, height: 40, borderRadius: 20, justifyContent: 'center', alignItems: 'center' },

  medicalCard: { marginHorizontal: spacing.screenPadding },
  medicalRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.surface.divider },
  medicalLabel: { fontSize: 14, fontWeight: '600', color: colors.text.muted },
  medicalValue: { fontSize: 14, fontWeight: '700', color: colors.text.primary },
  medicalNote: { fontSize: 13, color: colors.text.secondary, marginTop: spacing.md, lineHeight: 18 },
  tagRow: { flexDirection: 'row', gap: spacing.xs, flexWrap: 'wrap', flexShrink: 1, justifyContent: 'flex-end' },
  medicalTag: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  medicalTagText: { fontSize: 12, fontWeight: '600' },

  emptyTitle: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  emptyText: { fontSize: 13, color: colors.text.muted, marginTop: 4, lineHeight: 19 },

  modalBackdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', justifyContent: 'flex-end' },
  modalCard: { backgroundColor: colors.bg.elevated, padding: spacing.xl, borderTopLeftRadius: 24, borderTopRightRadius: 24, gap: spacing.md },
  modalTitle: { fontSize: 18, fontWeight: '800', color: colors.text.primary },
  input: { backgroundColor: colors.surface.divider, borderRadius: radius.md, paddingHorizontal: spacing.md, paddingVertical: spacing.md, color: colors.text.primary, fontSize: 15 },
  modalActions: { flexDirection: 'row', gap: spacing.md, marginTop: spacing.sm },
  modalButton: { flex: 1, paddingVertical: spacing.md, borderRadius: radius.md, alignItems: 'center' },
  modalCancel: { backgroundColor: colors.surface.divider },
  modalCancelText: { color: colors.text.muted, fontWeight: '700' },
  modalSave: { backgroundColor: '#EF4444' },
  modalSaveText: { color: '#FFF', fontWeight: '700' },
});
