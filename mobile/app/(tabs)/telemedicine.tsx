/**
 * Telemedicine — Premium Doctor Directory & Booking
 * Glassmorphism cards, doctor profiles, booking calendar
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
import { StaggeredList } from '../../src/components/AnimationSystem';
import { PillChip } from '../../src/components/PremiumComponents';

const DOCTORS = [
  { id: 1, name: 'Dr. Sarah Chen', specialty: 'Cardiologist', rating: 4.9, reviews: 128, available: true, nextSlot: '2:00 PM today', avatar: '👩‍⚕️', color: '#EF4444' },
  { id: 2, name: 'Dr. Michael Park', specialty: 'Dermatologist', rating: 4.8, reviews: 95, available: true, nextSlot: '4:30 PM today', avatar: '👨‍⚕️', color: '#F59E0B' },
  { id: 3, name: 'Dr. Emily Johnson', specialty: 'Psychiatrist', rating: 4.9, reviews: 210, available: false, nextSlot: 'Tomorrow 10:00 AM', avatar: '👩‍⚕️', color: '#8B5CF6' },
  { id: 4, name: 'Dr. James Wilson', specialty: 'General Practice', rating: 4.7, reviews: 156, available: true, nextSlot: '1:00 PM today', avatar: '👨‍⚕️', color: '#22C55E' },
  { id: 5, name: 'Dr. Lisa Anderson', specialty: 'Endocrinologist', rating: 4.8, reviews: 87, available: false, nextSlot: 'Wednesday 9:00 AM', avatar: '👩‍⚕️', color: '#06B6D4' },
];

const SPECIALTIES = ['All', 'Cardiology', 'Dermatology', 'Psychiatry', 'General', 'Endocrinology'];

export default function TelemedicineScreen() {
  const [selectedSpecialty, setSelectedSpecialty] = useState('All');

  return (
    <ScreenWrapper
      title="Telemedicine"
      subtitle="Connect with doctors instantly"
      gradient={['#3B82F6', '#06B6D4']}
      rightAction={{ icon: 'search', onPress: () => {} }}
    >
      {/* Quick Stats */}
      <View style={styles.statsRow}>
        <GlassCard variant="light" style={styles.statCard}>
          <ScoreRing score={95} size={60} strokeWidth={4} color={colors.health.calm} />
          <Text style={styles.statLabel}>Available</Text>
        </GlassCard>
        <GlassCard variant="light" style={styles.statCard}>
          <Text style={[styles.statValue, { color: colors.primary }]}>3</Text>
          <Text style={styles.statLabel}>Bookmarks</Text>
        </GlassCard>
        <GlassCard variant="light" style={styles.statCard}>
          <Text style={[styles.statValue, { color: '#F59E0B' }]}>1</Text>
          <Text style={styles.statLabel}>Upcoming</Text>
        </GlassCard>
      </View>

      {/* Specialty Filter */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterScroll}>
        <View style={styles.filterRow}>
          {SPECIALTIES.map(s => (
            <PillChip key={s} label={s} active={selectedSpecialty === s} onPress={() => setSelectedSpecialty(s)} />
          ))}
        </View>
      </ScrollView>

      {/* Doctor List */}
      <SectionHeaderPremium icon="people" iconColor="#3B82F6" title="Available Doctors" />
      <StaggeredList staggerDelay={100} animationType="slideIn">
        {DOCTORS.filter(d => selectedSpecialty === 'All' || d.specialty.toLowerCase().includes(selectedSpecialty.toLowerCase())).map(doctor => (
          <GlassCard key={doctor.id} variant="light" style={styles.doctorCard}>
            <View style={styles.doctorHeader}>
              <Text style={styles.doctorAvatar}>{doctor.avatar}</Text>
              <View style={{ flex: 1 }}>
                <Text style={styles.doctorName}>{doctor.name}</Text>
                <Text style={styles.doctorSpecialty}>{doctor.specialty}</Text>
                <View style={styles.ratingRow}>
                  <Ionicons name="star" size={14} color="#F59E0B" />
                  <Text style={styles.ratingText}>{doctor.rating}</Text>
                  <Text style={styles.reviewText}>({doctor.reviews} reviews)</Text>
                </View>
              </View>
              {doctor.available && (
                <View style={styles.availableBadge}>
                  <View style={styles.availableDot} />
                  <Text style={styles.availableText}>Available</Text>
                </View>
              )}
            </View>

            <View style={styles.slotRow}>
              <Ionicons name="time" size={14} color={colors.text.muted} />
              <Text style={styles.slotText}>Next: {doctor.nextSlot}</Text>
            </View>

            <View style={styles.doctorActions}>
              <TouchableOpacity style={[styles.bookBtn, { backgroundColor: doctor.color }]}>
                <Text style={styles.bookBtnText}>Book Now</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.profileBtn}>
                <Text style={styles.profileBtnText}>Profile</Text>
              </TouchableOpacity>
            </View>
          </GlassCard>
        ))}
      </StaggeredList>
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  statsRow: { flexDirection: 'row', gap: spacing.md, paddingHorizontal: spacing.screenPadding, marginBottom: spacing.lg },
  statCard: { flex: 1, alignItems: 'center', paddingVertical: spacing.md },
  statValue: { fontSize: 24, fontWeight: '800' },
  statLabel: { fontSize: 11, color: colors.text.muted, marginTop: 4 },

  filterScroll: { marginBottom: spacing.lg },
  filterRow: { flexDirection: 'row', paddingHorizontal: spacing.screenPadding, gap: spacing.sm },

  doctorCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.md },
  doctorHeader: { flexDirection: 'row', gap: spacing.md },
  doctorAvatar: { fontSize: 40 },
  doctorName: { fontSize: 16, fontWeight: '700', color: colors.text.primary },
  doctorSpecialty: { fontSize: 13, color: colors.text.muted, marginTop: 2 },
  ratingRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 4 },
  ratingText: { fontSize: 13, fontWeight: '700', color: '#F59E0B' },
  reviewText: { fontSize: 12, color: colors.text.muted },
  availableBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 8, paddingVertical: 4, backgroundColor: '#22C55E15', borderRadius: 6 },
  availableDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: '#22C55E' },
  availableText: { fontSize: 11, fontWeight: '600', color: '#22C55E' },

  slotRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: spacing.md, paddingVertical: spacing.sm, paddingHorizontal: spacing.md, backgroundColor: colors.bg.input, borderRadius: radius.md },
  slotText: { fontSize: 13, color: colors.text.secondary },

  doctorActions: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.md },
  bookBtn: { flex: 1, paddingVertical: spacing.md, borderRadius: radius.button, alignItems: 'center' },
  bookBtnText: { fontSize: 14, fontWeight: '700', color: '#FFF' },
  profileBtn: { flex: 1, paddingVertical: spacing.md, borderRadius: radius.button, alignItems: 'center', backgroundColor: colors.bg.elevated, borderWidth: 1, borderColor: colors.surface.border },
  profileBtnText: { fontSize: 14, fontWeight: '600', color: colors.text.secondary },
});
