/**
 * Emergency — Premium Emergency SOS & Contacts
 * Glassmorphism cards, animated SOS button, emergency contacts
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Dimensions, Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../../src/theme';
import { ScreenWrapper } from '../../src/components/ScreenWrapper';
import { GlassCard, SectionHeaderPremium, ScoreRing } from '../../src/components/PremiumComponents';
import { EmergencySOSButton } from '../../src/components/QuickActions';
import { Pulse } from '../../src/components/AnimationSystem';
import { SwipeableCard } from '../../src/components/GestureSystem';

const EMERGENCY_CONTACTS = [
  { id: 1, name: 'Emergency Services', phone: '911', icon: 'call', color: '#EF4444', priority: 'critical' },
  { id: 2, name: 'Dr. Smith (PCP)', phone: '(555) 123-4567', icon: 'medical', color: '#3B82F6', priority: 'high' },
  { id: 3, name: 'Mom', phone: '(555) 234-5678', icon: 'heart', color: '#EC4899', priority: 'high' },
  { id: 4, name: 'Dad', phone: '(555) 345-6789', icon: 'heart', color: '#F97316', priority: 'medium' },
  { id: 5, name: 'Pharmacy', phone: '(555) 456-7890', icon: 'medical', color: '#22C55E', priority: 'medium' },
];

const MEDICAL_INFO = {
  bloodType: 'O+',
  allergies: ['Penicillin', 'Peanuts'],
  medications: ['Vitamin D3', 'Omega-3'],
  conditions: [],
  insurance: 'Blue Cross #12345',
};

export default function EmergencyScreen() {
  const [sosActive, setSosActive] = useState(false);
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (sosActive) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 1.2, duration: 500, useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 1, duration: 500, useNativeDriver: true }),
        ])
      ).start();
    }
  }, [sosActive]);

  return (
    <ScreenWrapper
      title="Emergency"
      subtitle="Quick access to emergency services"
      gradient={['#EF4444', '#F97316']}
      rightAction={{ icon: 'settings', onPress: () => {} }}
    >
      {/* SOS Button */}
      <View style={styles.sosSection}>
        <View style={styles.sosContainer}>
          <Pulse color="#EF4444" size={140}>
            <TouchableOpacity
              style={[styles.sosButton, sosActive && styles.sosButtonActive]}
              onPress={() => setSosActive(!sosActive)}
            >
              <Ionicons name="call" size={36} color="#FFF" />
              <Text style={styles.sosLabel}>SOS</Text>
            </TouchableOpacity>
          </Pulse>
        </View>
        <Text style={styles.sosHint}>Tap to activate emergency alert</Text>
        {sosActive && (
          <View style={styles.sosActiveBanner}>
            <Ionicons name="warning" size={16} color="#EF4444" />
            <Text style={styles.sosActiveText}>Emergency mode active — sharing location with contacts</Text>
          </View>
        )}
      </View>

      {/* Emergency Contacts */}
      <SectionHeaderPremium icon="people" iconColor="#EF4444" title="Emergency Contacts" action={{ label: 'Add', onPress: () => {} }} />
      {EMERGENCY_CONTACTS.map((contact, i) => (
        <SwipeableCard
          key={contact.id}
          onSwipeLeft={() => {}}
          onSwipeRight={() => {}}
          rightAction={{ icon: 'call', color: '#22C55E', label: 'Call' }}
        >
          <GlassCard variant="light" style={styles.contactCard}>
            <View style={styles.contactRow}>
              <View style={[styles.contactIcon, { backgroundColor: contact.color + '15' }]}>
                <Ionicons name={contact.icon as any} size={20} color={contact.color} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.contactName}>{contact.name}</Text>
                <Text style={styles.contactPhone}>{contact.phone}</Text>
              </View>
              <TouchableOpacity style={[styles.callBtn, { backgroundColor: '#22C55E15' }]}>
                <Ionicons name="call" size={18} color="#22C55E" />
              </TouchableOpacity>
            </View>
          </GlassCard>
        </SwipeableCard>
      ))}

      {/* Medical Info */}
      <SectionHeaderPremium icon="medical" iconColor="#3B82F6" title="Medical Info" />
      <GlassCard variant="light" style={styles.medicalCard}>
        <View style={styles.medicalRow}>
          <Text style={styles.medicalLabel}>Blood Type</Text>
          <Text style={[styles.medicalValue, { color: '#EF4444' }]}>{MEDICAL_INFO.bloodType}</Text>
        </View>
        <View style={styles.medicalRow}>
          <Text style={styles.medicalLabel}>Allergies</Text>
          <View style={styles.tagRow}>
            {MEDICAL_INFO.allergies.map((a, i) => (
              <View key={i} style={[styles.medicalTag, { backgroundColor: '#EF444415' }]}>
                <Text style={[styles.medicalTagText, { color: '#EF4444' }]}>{a}</Text>
              </View>
            ))}
          </View>
        </View>
        <View style={styles.medicalRow}>
          <Text style={styles.medicalLabel}>Medications</Text>
          <View style={styles.tagRow}>
            {MEDICAL_INFO.medications.map((m, i) => (
              <View key={i} style={[styles.medicalTag, { backgroundColor: '#3B82F615' }]}>
                <Text style={[styles.medicalTagText, { color: '#3B82F6' }]}>{m}</Text>
              </View>
            ))}
          </View>
        </View>
        <View style={styles.medicalRow}>
          <Text style={styles.medicalLabel}>Insurance</Text>
          <Text style={styles.medicalValue}>{MEDICAL_INFO.insurance}</Text>
        </View>
      </GlassCard>
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  sosSection: { alignItems: 'center', paddingVertical: spacing.xl, paddingHorizontal: spacing.screenPadding },
  sosContainer: { marginBottom: spacing.md },
  sosButton: { width: 100, height: 100, borderRadius: 50, backgroundColor: '#EF4444', justifyContent: 'center', alignItems: 'center' },
  sosButtonActive: { backgroundColor: '#DC2626' },
  sosLabel: { fontSize: 16, fontWeight: '800', color: '#FFF', marginTop: 4 },
  sosHint: { fontSize: 13, color: colors.text.muted, marginTop: spacing.sm },
  sosActiveBanner: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginTop: spacing.md, paddingHorizontal: spacing.lg, paddingVertical: spacing.md, backgroundColor: '#EF444415', borderRadius: radius.md, borderWidth: 1, borderColor: '#EF444430' },
  sosActiveText: { fontSize: 12, color: '#EF4444', fontWeight: '600', flex: 1 },

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
  tagRow: { flexDirection: 'row', gap: spacing.xs },
  medicalTag: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  medicalTagText: { fontSize: 12, fontWeight: '600' },
});
