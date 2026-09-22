/**
 * Telemedicine — the doctor directory and booking.
 *
 * The directory is sample data, not a connected telehealth provider, and the
 * screen says so where it cannot be missed. Someone who books here must not
 * come away believing a clinician is expecting them: the confirmation repeats
 * it, because that is the moment the belief forms.
 */
import React, { useCallback, useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { colors, spacing, radius } from '../../src/theme';
import { ScreenWrapper } from '../../src/components/ScreenWrapper';
import { GlassCard, SectionHeaderPremium } from '../../src/components/PremiumComponents';
import { useApis } from '../../src/hooks/useApi';
import { getJson, postJson, asArray } from '../../src/services/http';
import { useUserStore } from '../../src/stores';

interface Doctor {
  id: string;
  name: string;
  specialty: string;
  rating: number;
  reviews: number;
  bio: string;
  consultation_fee: number;
  available_today: boolean;
  languages: string[];
}

interface Appointment {
  id: string;
  doctor: string;
  specialty: string;
  date: string;
  time: string;
  fee: number;
  status: string;
}

const SPECIALTY_COLOR: Record<string, string> = {
  Cardiology: '#EF4444',
  Dermatology: '#F59E0B',
  Psychiatry: '#8B5CF6',
  'General Practice': '#22C55E',
  Endocrinology: '#06B6D4',
};

function colorFor(specialty: string): string {
  return SPECIALTY_COLOR[specialty] ?? colors.primary;
}

function todayPlus(days: number): string {
  return new Date(Date.now() + days * 86400_000).toISOString().slice(0, 10);
}

export default function TelemedicineScreen() {
  const userId = useUserStore((s) => s.userId);
  const [specialty, setSpecialty] = useState('All');
  const [booking, setBooking] = useState<string | null>(null);

  const { data, loading, refreshing, refresh, reload } = useApis<{
    doctors: { doctors: Doctor[]; notice?: string; directory?: string };
    specialties: { specialties: string[] };
    appointments: { appointments: Appointment[] };
  }>({
    doctors: specialty === 'All'
      ? '/telemedicine/doctors'
      : `/telemedicine/doctors?specialty=${encodeURIComponent(specialty)}`,
    specialties: '/telemedicine/specialties',
    appointments: `/telemedicine/appointments/${userId}`,
  });

  const doctors = asArray<Doctor>(data.doctors?.doctors);
  const specialties = ['All', ...asArray<string>(data.specialties?.specialties)];
  const appointments = asArray<Appointment>(data.appointments?.appointments);
  const isSample = data.doctors?.directory === 'sample';

  const book = useCallback(async (doctor: Doctor) => {
    // Booked for tomorrow, so availability is asked for that date rather
    // than today, whose slots may already have passed.
    const date = todayPlus(1);
    const slots = await getJson<{ available_slots?: string[] }>(
      `/telemedicine/doctors/${doctor.id}/availability?date=${date}`
    );
    const slot = asArray<string>(slots?.available_slots)[0];
    if (!slot) {
      Alert.alert('No slots', `${doctor.name} has no times listed.`);
      return;
    }

    setBooking(doctor.id);
    const result = await postJson<{ appointment?: Appointment; notice?: string; error?: string }>(
      '/telemedicine/appointments',
      {
        patient_id: userId,
        doctor_id: doctor.id,
        date,
        time_slot: slot,
        consultation_type: 'video',
      }
    );
    setBooking(null);

    if (!result?.appointment) {
      Alert.alert('Not booked', result?.error ?? 'The appointment could not be booked.');
      return;
    }
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    Alert.alert(
      'Saved in this app only',
      `${result.appointment.doctor} · ${result.appointment.date} at ${result.appointment.time}.\n\n${
        result.notice ?? 'This directory is sample data. No clinician has been contacted.'
      }`
    );
    await reload();
  }, [userId, reload]);

  return (
    <ScreenWrapper
      title="Telemedicine"
      subtitle="Doctor directory and booking"
      gradient={['#3B82F6', '#06B6D4']}
      loading={loading}
      refreshing={refreshing}
      onRefresh={refresh}
    >
      {isSample && (
        <GlassCard variant="light" style={styles.noticeCard}>
          <View style={styles.noticeRow}>
            <Ionicons name="information-circle" size={20} color="#F59E0B" />
            <Text style={styles.noticeText}>
              {data.doctors?.notice}
              {' '}Bookings are kept in this app and reach nobody.
            </Text>
          </View>
        </GlassCard>
      )}

      {appointments.length > 0 && (
        <>
          <SectionHeaderPremium icon="calendar" iconColor="#22C55E" title="Your Appointments" />
          {appointments.map((appointment) => (
            <GlassCard key={appointment.id} variant="light" style={styles.doctorCard}>
              <Text style={styles.doctorName}>{appointment.doctor}</Text>
              <Text style={styles.doctorSpecialty}>
                {appointment.specialty} · {appointment.date} at {appointment.time}
              </Text>
              <Text style={styles.appointmentStatus}>{appointment.status}</Text>
            </GlassCard>
          ))}
        </>
      )}

      <SectionHeaderPremium icon="medkit" iconColor="#3B82F6" title="Find a Doctor" />
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterScroll}>
        <View style={styles.filterRow}>
          {specialties.map((option) => {
            const on = option === specialty;
            return (
              <TouchableOpacity
                key={option}
                style={[styles.filterChip, on && styles.filterChipOn]}
                onPress={() => setSpecialty(option)}
                accessibilityRole="radio"
                accessibilityState={{ selected: on }}
              >
                <Text style={[styles.filterText, on && styles.filterTextOn]}>{option}</Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </ScrollView>

      {doctors.length === 0 ? (
        <GlassCard variant="light" style={styles.doctorCard}>
          <Text style={styles.doctorSpecialty}>No clinicians listed for that specialty.</Text>
        </GlassCard>
      ) : (
        doctors.map((doctor) => {
          const tint = colorFor(doctor.specialty);
          return (
            <GlassCard key={doctor.id} variant="light" style={styles.doctorCard}>
              <View style={styles.doctorHeader}>
                <View style={[styles.doctorAvatar, { backgroundColor: tint + '15' }]}>
                  <Ionicons name="person" size={20} color={tint} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.doctorName}>{doctor.name}</Text>
                  <Text style={styles.doctorSpecialty}>{doctor.specialty}</Text>
                  <View style={styles.ratingRow}>
                    <Ionicons name="star" size={12} color="#F59E0B" />
                    <Text style={styles.ratingText}>{doctor.rating}</Text>
                    <Text style={styles.reviewText}>({doctor.reviews} reviews)</Text>
                  </View>
                </View>
                {doctor.available_today && (
                  <View style={styles.availableBadge}>
                    <View style={styles.availableDot} />
                    <Text style={styles.availableText}>Today</Text>
                  </View>
                )}
              </View>
              <Text style={styles.doctorBio}>{doctor.bio}</Text>
              <View style={styles.slotRow}>
                <Ionicons name="cash-outline" size={14} color={colors.text.muted} />
                <Text style={styles.slotText}>
                  {doctor.consultation_fee} per consultation · {doctor.languages?.join(', ')}
                </Text>
              </View>
              <TouchableOpacity
                style={[styles.bookBtn, { backgroundColor: tint }]}
                onPress={() => book(doctor)}
                disabled={booking === doctor.id}
                accessibilityRole="button"
                accessibilityLabel={`Book with ${doctor.name}`}
              >
                <Text style={styles.bookBtnText}>
                  {booking === doctor.id ? 'Booking…' : 'Book a slot'}
                </Text>
              </TouchableOpacity>
            </GlassCard>
          );
        })
      )}
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  noticeCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.md, marginTop: spacing.md },
  noticeRow: { flexDirection: 'row', gap: spacing.sm },
  noticeText: { flex: 1, fontSize: 12, color: colors.text.muted, lineHeight: 18 },

  filterScroll: { marginBottom: spacing.lg },
  filterRow: { flexDirection: 'row', paddingHorizontal: spacing.screenPadding, gap: spacing.sm },
  filterChip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 999, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border },
  filterChipOn: { backgroundColor: colors.primary, borderColor: colors.primary },
  filterText: { fontSize: 12, fontWeight: '600', color: colors.text.muted },
  filterTextOn: { color: '#FFF' },

  doctorCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.md },
  doctorHeader: { flexDirection: 'row', gap: spacing.md },
  doctorAvatar: { width: 40, height: 40, borderRadius: 20, justifyContent: 'center', alignItems: 'center' },
  doctorName: { fontSize: 16, fontWeight: '700', color: colors.text.primary },
  doctorSpecialty: { fontSize: 13, color: colors.text.muted, marginTop: 2 },
  doctorBio: { fontSize: 13, color: colors.text.secondary, marginTop: spacing.md, lineHeight: 18 },
  appointmentStatus: { fontSize: 12, color: '#22C55E', fontWeight: '700', marginTop: 4, textTransform: 'capitalize' },
  ratingRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 4 },
  ratingText: { fontSize: 13, fontWeight: '700', color: '#F59E0B' },
  reviewText: { fontSize: 12, color: colors.text.muted },
  availableBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 8, paddingVertical: 4, backgroundColor: '#22C55E15', borderRadius: 6, alignSelf: 'flex-start' },
  availableDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: '#22C55E' },
  availableText: { fontSize: 11, fontWeight: '600', color: '#22C55E' },

  slotRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: spacing.md, paddingVertical: spacing.sm, paddingHorizontal: spacing.md, backgroundColor: colors.bg.input, borderRadius: radius.md },
  slotText: { fontSize: 13, color: colors.text.secondary, flex: 1 },

  bookBtn: { paddingVertical: spacing.md, borderRadius: radius.button, alignItems: 'center', marginTop: spacing.md },
  bookBtnText: { fontSize: 14, fontWeight: '700', color: '#FFF' },
});
