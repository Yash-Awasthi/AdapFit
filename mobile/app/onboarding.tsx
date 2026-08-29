/**
 * Onboarding — 5-Step Animated Health Profile Setup
 * Premium glassmorphism design with animated transitions,
 * health goal selection, device pairing, and personalized setup.
 */
import React, { useState, useRef } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Animated, Dimensions, TextInput, StatusBar, Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';
import { colors, spacing, radius, typography } from '../src/theme';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

// ─── Step Data ────────────────────────────────────────────────
const HEALTH_GOALS = [
  { id: 'weight_loss', icon: 'scale', label: 'Weight Loss', color: '#F97316' },
  { id: 'muscle_gain', icon: 'barbell', label: 'Muscle Gain', color: '#EF4444' },
  { id: 'better_sleep', icon: 'moon', label: 'Better Sleep', color: '#8B5CF6' },
  { id: 'reduce_stress', icon: 'leaf', label: 'Reduce Stress', color: '#10B981' },
  { id: 'improve_fitness', icon: 'fitness', label: 'Fitness', color: '#06B6D4' },
  { id: 'mental_wellness', icon: 'heart', label: 'Mental Health', color: '#A78BFA' },
  { id: 'chronic_condition', icon: 'medical', label: 'Manage Condition', color: '#F59E0B' },
  { id: 'general_wellness', icon: 'nutrition', label: 'General Wellness', color: '#22C55E' },
];

const GENDER_OPTIONS = [
  { id: 'male', icon: 'male', label: 'Male', color: '#3B82F6' },
  { id: 'female', icon: 'female', label: 'Female', color: '#EC4899' },
  { id: 'non_binary', icon: 'person', label: 'Non-Binary', color: '#A78BFA' },
  { id: 'prefer_not', icon: 'help-circle', label: 'Prefer Not to Say', color: '#64748B' },
];

const DEVICE_OPTIONS = [
  { id: 'apple_watch', icon: 'watch', label: 'Apple Watch', color: '#F1F5F9' },
  { id: 'fitbit', icon: 'watch-outline', label: 'Fitbit', color: '#00B0B9' },
  { id: 'garmin', icon: 'watch', label: 'Garmin', color: '#000' },
  { id: 'samsung', icon: 'watch', label: 'Samsung Health', color: '#1428A0' },
  { id: 'google_fit', icon: 'logo-google', label: 'Google Fit', color: '#4285F4' },
  { id: 'oura', icon: 'radio-button-on', label: 'Oura Ring', color: '#C4B5A0' },
  { id: 'none', icon: 'phone-portrait', label: 'Phone Only', color: '#64748B' },
];

const ACTIVITY_LEVELS = [
  { id: 'sedentary', label: 'Sedentary', desc: 'Little to no exercise', icon: '-bed', color: '#64748B' },
  { id: 'light', label: 'Lightly Active', desc: '1-3 days/week', icon: 'walk', color: '#22C55E' },
  { id: 'moderate', label: 'Moderately Active', desc: '3-5 days/week', icon: 'bicycle', color: '#F59E0B' },
  { id: 'very', label: 'Very Active', desc: '6-7 days/week', icon: 'fitness', color: '#F97316' },
  { id: 'extreme', label: 'Athlete', desc: '2x/day or intense', icon: 'flame', color: '#EF4444' },
];

const SLEEP_GOALS = [
  { hours: 6, label: '6 hrs', desc: 'Minimum' },
  { hours: 7, label: '7 hrs', desc: 'Recommended' },
  { hours: 8, label: '8 hrs', desc: 'Optimal' },
  { hours: 9, label: '9 hrs', desc: 'Extended' },
];

// ─── Animated Step Indicator ──────────────────────────────────
function StepIndicator({ current, total }: { current: number; total: number }) {
  return (
    <View style={styles.stepIndicator}>
      {Array.from({ length: total }).map((_, i) => (
        <View
          key={i}
          style={[
            styles.stepDot,
            i === current && styles.stepDotActive,
            i < current && styles.stepDotCompleted,
          ]}
        />
      ))}
    </View>
  );
}

// ─── Selectable Card ──────────────────────────────────────────
function SelectableCard({ icon, label, desc, color, selected, onPress }: {
  icon: string; label: string; desc?: string; color: string; selected: boolean; onPress: () => void;
}) {
  return (
    <TouchableOpacity
      onPress={onPress}
      activeOpacity={0.7}
      style={[styles.selectableCard, selected && { borderColor: color, backgroundColor: color + '15' }]}
    >
      <View style={[styles.selectableIcon, { backgroundColor: color + '20' }]}>
        <Ionicons name={icon as any} size={22} color={color} />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={[typography.body.md, { color: selected ? color : colors.text.primary, fontWeight: selected ? '700' : '500' }]}>{label}</Text>
        {desc && <Text style={[typography.body.sm, { color: colors.text.muted, marginTop: 2 }]}>{desc}</Text>}
      </View>
      {selected && (
        <View style={[styles.checkCircle, { backgroundColor: color }]}>
          <Ionicons name="checkmark" size={14} color="#fff" />
        </View>
      )}
    </TouchableOpacity>
  );
}

// ─── Step 1: Welcome ──────────────────────────────────────────
function WelcomeStep({ onNext }: { onNext: () => void }) {
  return (
    <LinearGradient colors={['#6366F1', '#8B5CF6', '#0F1629']} style={styles.stepContainer}>
      <View style={styles.welcomeContent}>
        <View style={styles.logoContainer}>
          <Ionicons name="fitness" size={64} color="#fff" />
        </View>
        <Text style={[typography.heading.hero, { color: '#fff', textAlign: 'center' }]}>Welcome to{'\n'}AdapFit</Text>
        <Text style={[typography.body.lg, { color: 'rgba(255,255,255,0.7)', textAlign: 'center', marginTop: 16, lineHeight: 26 }]}>
          Your AI-powered health companion.{'\n'}Let's personalize your experience.
        </Text>
        <TouchableOpacity onPress={onNext} style={styles.primaryButton}>
          <Text style={styles.primaryButtonText}>Get Started</Text>
          <Ionicons name="arrow-forward" size={20} color="#fff" />
        </TouchableOpacity>
        <TouchableOpacity onPress={onNext} style={{ marginTop: 16 }}>
          <Text style={[typography.body.md, { color: 'rgba(255,255,255,0.5)' }]}>Skip for now</Text>
        </TouchableOpacity>
      </View>
    </LinearGradient>
  );
}

// ─── Step 2: Health Goals ─────────────────────────────────────
function GoalsStep({ selected, onToggle, onNext, onBack }: {
  selected: string[]; onToggle: (id: string) => void; onNext: () => void; onBack: () => void;
}) {
  return (
    <View style={styles.stepContainerLight}>
      <Text style={[typography.heading.h1, { marginBottom: 8 }]}>Health Goals</Text>
      <Text style={[typography.body.lg, { color: colors.text.muted, marginBottom: 24 }]}>What do you want to improve?</Text>
      <View style={styles.goalsGrid}>
        {HEALTH_GOALS.map((goal) => (
          <SelectableCard
            key={goal.id}
            icon={goal.icon}
            label={goal.label}
            color={goal.color}
            selected={selected.includes(goal.id)}
            onPress={() => onToggle(goal.id)}
          />
        ))}
      </View>
      <View style={styles.stepActions}>
        <TouchableOpacity onPress={onBack} style={styles.secondaryButton}>
          <Ionicons name="arrow-back" size={20} color={colors.text.primary} />
          <Text style={styles.secondaryButtonText}>Back</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={onNext} style={[styles.primaryButton, { opacity: selected.length > 0 ? 1 : 0.5 }]} disabled={selected.length === 0}>
          <Text style={styles.primaryButtonText}>Continue</Text>
          <Ionicons name="arrow-forward" size={20} color="#fff" />
        </TouchableOpacity>
      </View>
    </View>
  );
}

// ─── Step 3: Personal Info ────────────────────────────────────
function PersonalInfoStep({ gender, setGender, age, setAge, weight, setWeight, height, setHeight, onNext, onBack }: {
  gender: string; setGender: (g: string) => void;
  age: string; setAge: (a: string) => void;
  weight: string; setWeight: (w: string) => void;
  height: string; setHeight: (h: string) => void;
  onNext: () => void; onBack: () => void;
}) {
  return (
    <View style={styles.stepContainerLight}>
      <Text style={[typography.heading.h1, { marginBottom: 8 }]}>About You</Text>
      <Text style={[typography.body.lg, { color: colors.text.muted, marginBottom: 24 }]}>This helps us personalize your plan</Text>
      
      <Text style={[typography.label.md, { color: colors.text.muted, marginBottom: 8 }]}>Gender</Text>
      <View style={styles.genderGrid}>
        {GENDER_OPTIONS.map((g) => (
          <SelectableCard
            key={g.id}
            icon={g.icon}
            label={g.label}
            color={g.color}
            selected={gender === g.id}
            onPress={() => setGender(g.id)}
          />
        ))}
      </View>

      <View style={styles.inputRow}>
        <View style={styles.inputContainer}>
          <Text style={[typography.label.sm, { color: colors.text.muted, marginBottom: 6 }]}>Age</Text>
          <TextInput
            style={styles.input}
            value={age}
            onChangeText={setAge}
            placeholder="25"
            placeholderTextColor={colors.text.muted}
            keyboardType="number-pad"
          />
        </View>
        <View style={styles.inputContainer}>
          <Text style={[typography.label.sm, { color: colors.text.muted, marginBottom: 6 }]}>Weight (kg)</Text>
          <TextInput
            style={styles.input}
            value={weight}
            onChangeText={setWeight}
            placeholder="70"
            placeholderTextColor={colors.text.muted}
            keyboardType="number-pad"
          />
        </View>
        <View style={styles.inputContainer}>
          <Text style={[typography.label.sm, { color: colors.text.muted, marginBottom: 6 }]}>Height (cm)</Text>
          <TextInput
            style={styles.input}
            value={height}
            onChangeText={setHeight}
            placeholder="175"
            placeholderTextColor={colors.text.muted}
            keyboardType="number-pad"
          />
        </View>
      </View>

      <View style={styles.stepActions}>
        <TouchableOpacity onPress={onBack} style={styles.secondaryButton}>
          <Ionicons name="arrow-back" size={20} color={colors.text.primary} />
          <Text style={styles.secondaryButtonText}>Back</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={onNext} style={styles.primaryButton}>
          <Text style={styles.primaryButtonText}>Continue</Text>
          <Ionicons name="arrow-forward" size={20} color="#fff" />
        </TouchableOpacity>
      </View>
    </View>
  );
}

// ─── Step 4: Device Pairing ───────────────────────────────────
function DeviceStep({ selected, onSelect, onNext, onBack }: {
  selected: string; onSelect: (id: string) => void; onNext: () => void; onBack: () => void;
}) {
  return (
    <View style={styles.stepContainerLight}>
      <Text style={[typography.heading.h1, { marginBottom: 8 }]}>Connect Devices</Text>
      <Text style={[typography.body.lg, { color: colors.text.muted, marginBottom: 24 }]}>Sync your wearables for better insights</Text>
      <View style={styles.deviceGrid}>
        {DEVICE_OPTIONS.map((device) => (
          <SelectableCard
            key={device.id}
            icon={device.icon}
            label={device.label}
            color={device.color}
            selected={selected === device.id}
            onPress={() => onSelect(device.id)}
          />
        ))}
      </View>
      <View style={styles.stepActions}>
        <TouchableOpacity onPress={onBack} style={styles.secondaryButton}>
          <Ionicons name="arrow-back" size={20} color={colors.text.primary} />
          <Text style={styles.secondaryButtonText}>Back</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={onNext} style={styles.primaryButton}>
          <Text style={styles.primaryButtonText}>Continue</Text>
          <Ionicons name="arrow-forward" size={20} color="#fff" />
        </TouchableOpacity>
      </View>
    </View>
  );
}

// ─── Step 5: Activity & Sleep Preferences ─────────────────────
function PreferencesStep({ activityLevel, setActivityLevel, sleepGoal, setSleepGoal, onNext, onBack }: {
  activityLevel: string; setActivityLevel: (a: string) => void;
  sleepGoal: number; setSleepGoal: (s: number) => void;
  onNext: () => void; onBack: () => void;
}) {
  return (
    <View style={styles.stepContainerLight}>
      <Text style={[typography.heading.h1, { marginBottom: 8 }]}>Your Lifestyle</Text>
      <Text style={[typography.body.lg, { color: colors.text.muted, marginBottom: 24 }]}>Help us tailor recommendations</Text>

      <Text style={[typography.label.md, { color: colors.text.muted, marginBottom: 10 }]}>Activity Level</Text>
      <View style={styles.activityGrid}>
        {ACTIVITY_LEVELS.map((level) => (
          <SelectableCard
            key={level.id}
            icon={level.icon}
            label={level.label}
            desc={level.desc}
            color={level.color}
            selected={activityLevel === level.id}
            onPress={() => setActivityLevel(level.id)}
          />
        ))}
      </View>

      <Text style={[typography.label.md, { color: colors.text.muted, marginBottom: 10, marginTop: 20 }]}>Sleep Goal</Text>
      <View style={styles.sleepGrid}>
        {SLEEP_GOALS.map((goal) => (
          <TouchableOpacity
            key={goal.hours}
            onPress={() => setSleepGoal(goal.hours)}
            style={[styles.sleepCard, sleepGoal === goal.hours && { borderColor: colors.health.sleep, backgroundColor: colors.health.sleep + '15' }]}
          >
            <Text style={[typography.metric.small, { color: sleepGoal === goal.hours ? colors.health.sleep : colors.text.primary }]}>{goal.hours}</Text>
            <Text style={[typography.body.xs, { color: colors.text.muted, marginTop: 2 }]}>{goal.desc}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.stepActions}>
        <TouchableOpacity onPress={onBack} style={styles.secondaryButton}>
          <Ionicons name="arrow-back" size={20} color={colors.text.primary} />
          <Text style={styles.secondaryButtonText}>Back</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={onNext} style={styles.primaryButton}>
          <Text style={styles.primaryButtonText}>Start Using AdapFit</Text>
          <Ionicons name="checkmark-circle" size={20} color="#fff" />
        </TouchableOpacity>
      </View>
    </View>
  );
}

// ═══════════════════════════════════════════════════════════════
// ─── MAIN ONBOARDING ─────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════
export default function OnboardingScreen() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [selectedGoals, setSelectedGoals] = useState<string[]>([]);
  const [gender, setGender] = useState('');
  const [age, setAge] = useState('');
  const [weight, setWeight] = useState('');
  const [height, setHeight] = useState('');
  const [device, setDevice] = useState('');
  const [activityLevel, setActivityLevel] = useState('');
  const [sleepGoal, setSleepGoal] = useState(8);

  const toggleGoal = (id: string) => {
    setSelectedGoals(prev => prev.includes(id) ? prev.filter(g => g !== id) : [...prev, id]);
  };

  const goNext = () => {
    if (step < 4) setStep(step + 1);
    else router.replace('/(tabs)');
  };
  const goBack = () => { if (step > 0) setStep(step - 1); };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
      {step > 0 && (
        <View style={styles.topBar}>
          <StepIndicator current={step} total={5} />
          <Text style={[typography.body.sm, { color: colors.text.muted }]}>Step {step} of 5</Text>
        </View>
      )}
      <ScrollView contentContainerStyle={{ flexGrow: 1 }} showsVerticalScrollIndicator={false}>
        {step === 0 && <WelcomeStep onNext={goNext} />}
        {step === 1 && <GoalsStep selected={selectedGoals} onToggle={toggleGoal} onNext={goNext} onBack={goBack} />}
        {step === 2 && <PersonalInfoStep gender={gender} setGender={setGender} age={age} setAge={setAge} weight={weight} setWeight={setWeight} height={height} setHeight={setHeight} onNext={goNext} onBack={goBack} />}
        {step === 3 && <DeviceStep selected={device} onSelect={setDevice} onNext={goNext} onBack={goBack} />}
        {step === 4 && <PreferencesStep activityLevel={activityLevel} setActivityLevel={setActivityLevel} sleepGoal={sleepGoal} setSleepGoal={setSleepGoal} onNext={goNext} onBack={goBack} />}
      </ScrollView>
    </View>
  );
}

// ═══════════════════════════════════════════════════════════════
// ─── STYLES ──────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  stepContainer: { flex: 1, paddingTop: Platform.OS === 'ios' ? 80 : 60, paddingHorizontal: spacing.screenPadding },
  stepContainerLight: { paddingTop: 20, paddingHorizontal: spacing.screenPadding },
  topBar: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingTop: Platform.OS === 'ios' ? 60 : 40, paddingHorizontal: spacing.screenPadding },

  // Welcome
  welcomeContent: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  logoContainer: {
    width: 120, height: 120, borderRadius: 60,
    backgroundColor: 'rgba(255,255,255,0.1)', borderWidth: 2, borderColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center', alignItems: 'center', marginBottom: 32,
  },

  // Step indicator
  stepIndicator: { flexDirection: 'row', gap: 8 },
  stepDot: { width: 32, height: 4, borderRadius: 2, backgroundColor: colors.surface.border },
  stepDotActive: { width: 32, backgroundColor: colors.primary },
  stepDotCompleted: { width: 32, backgroundColor: colors.health.success },

  // Cards
  goalsGrid: { gap: 10 },
  genderGrid: { gap: 10, marginBottom: 20 },
  deviceGrid: { gap: 10 },
  activityGrid: { gap: 10 },
  sleepGrid: { flexDirection: 'row', gap: 10 },
  sleepCard: {
    flex: 1, alignItems: 'center', backgroundColor: colors.bg.card,
    borderRadius: 16, padding: 14, borderWidth: 1, borderColor: colors.surface.border,
  },

  selectableCard: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    backgroundColor: colors.bg.card, borderRadius: 14, padding: 14,
    borderWidth: 1.5, borderColor: colors.surface.border,
  },
  selectableIcon: {
    width: 40, height: 40, borderRadius: 12,
    justifyContent: 'center', alignItems: 'center',
  },
  checkCircle: {
    width: 24, height: 24, borderRadius: 12,
    justifyContent: 'center', alignItems: 'center',
  },

  // Inputs
  inputRow: { flexDirection: 'row', gap: 10, marginBottom: 20 },
  inputContainer: { flex: 1 },
  input: {
    backgroundColor: colors.bg.card, borderRadius: 12, padding: 14,
    borderWidth: 1, borderColor: colors.surface.border,
    color: colors.text.primary, fontSize: 16, textAlign: 'center',
  },

  // Actions
  stepActions: { flexDirection: 'row', justifyContent: 'space-between', paddingTop: 24, paddingBottom: 40 },
  primaryButton: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    backgroundColor: colors.primary, paddingHorizontal: 28, paddingVertical: 16,
    borderRadius: radius.button,
  },
  primaryButtonText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  secondaryButton: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: colors.bg.card, paddingHorizontal: 20, paddingVertical: 16,
    borderRadius: radius.button, borderWidth: 1, borderColor: colors.surface.border,
  },
  secondaryButtonText: { color: colors.text.primary, fontSize: 16, fontWeight: '600' },
});
