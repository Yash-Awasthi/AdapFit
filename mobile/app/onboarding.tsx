import React, { useState } from "react";
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView, Dimensions
} from "react-native";
import { useRouter } from "expo-router";
import {
  Target, Dumbbell, Calendar, AlertCircle, ChevronRight, ChevronLeft,
  Zap, Moon, Heart, Activity
} from "lucide-react-native";

const { width } = Dimensions.get("window");

const GOALS = [
  { id: "strength", label: "Build Strength", icon: Dumbbell },
  { id: "hypertrophy", label: "Build Muscle", icon: Activity },
  { id: "fat_loss", label: "Lose Fat", icon: Zap },
  { id: "endurance", label: "Improve Endurance", icon: Heart },
  { id: "recovery", label: "Better Recovery", icon: Moon },
  { id: "general", label: "General Fitness", icon: Target },
];

const EXPERIENCE = [
  { id: "beginner", label: "Beginner", desc: "< 6 months training" },
  { id: "intermediate", label: "Intermediate", desc: "6 months - 2 years" },
  { id: "advanced", label: "Advanced", desc: "2+ years consistent" },
  { id: "elite", label: "Elite", desc: "Competitive / coached" },
];

const EQUIPMENT = [
  { id: "full_gym", label: "Full Gym" },
  { id: "home_gym", label: "Home Gym" },
  { id: "dumbbells_only", label: "Dumbbells Only" },
  { id: "bodyweight", label: "Bodyweight Only" },
  { id: "resistance_bands", label: "Resistance Bands" },
];

const SCHEDULE = [
  { id: "2", label: "2 days/week" },
  { id: "3", label: "3 days/week" },
  { id: "4", label: "4 days/week" },
  { id: "5", label: "5 days/week" },
  { id: "6", label: "6 days/week" },
];

const INJURY_OPTIONS = [
  { id: "none", label: "No injuries" },
  { id: "lower_back", label: "Lower back" },
  { id: "knee", label: "Knee" },
  { id: "shoulder", label: "Shoulder" },
  { id: "wrist", label: "Wrist" },
  { id: "hip", label: "Hip" },
];

export default function OnboardingScreen() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [goals, setGoals] = useState<string[]>([]);
  const [experience, setExperience] = useState("");
  const [equipment, setEquipment] = useState<string[]>([]);
  const [schedule, setSchedule] = useState("");
  const [injuries, setInjuries] = useState<string[]>([]);

  const toggleItem = (arr: string[], setArr: (v: string[]) => void, id: string) => {
    setArr(arr.includes(id) ? arr.filter((x) => x !== id) : [...arr, id]);
  };

  const next = () => setStep(Math.min(step + 1, 4));
  const prev = () => setStep(Math.max(step - 1, 0));

  const complete = () => {
    // TODO: POST to /api/v1/users onboarding endpoint
    router.replace("/(tabs)");
  };

  const renderStep = () => {
    switch (step) {
      case 0:
        return (
          <View>
            <Text style={styles.stepTitle}>What are your goals?</Text>
            <Text style={styles.stepSub}>Select one or more</Text>
            {GOALS.map((g) => {
              const Icon = g.icon;
              const sel = goals.includes(g.id);
              return (
                <TouchableOpacity
                  key={g.id}
                  style={[styles.optionCard, sel && styles.optionSelected]}
                  onPress={() => toggleItem(goals, setGoals, g.id)}
                >
                  <Icon size={20} color={sel ? "#818CF8" : "#64748B"} />
                  <Text style={[styles.optionText, sel && styles.optionTextSelected]}>{g.label}</Text>
                </TouchableOpacity>
              );
            })}
          </View>
        );
      case 1:
        return (
          <View>
            <Text style={styles.stepTitle}>Your experience level</Text>
            <Text style={styles.stepSub}>This helps us calibrate intensity</Text>
            {EXPERIENCE.map((e) => (
              <TouchableOpacity
                key={e.id}
                style={[styles.optionCard, experience === e.id && styles.optionSelected]}
                onPress={() => setExperience(e.id)}
              >
                <Text style={[styles.optionText, experience === e.id && styles.optionTextSelected]}>
                  {e.label}
                </Text>
                <Text style={styles.optionDesc}>{e.desc}</Text>
              </TouchableOpacity>
            ))}
          </View>
        );
      case 2:
        return (
          <View>
            <Text style={styles.stepTitle}>Equipment available</Text>
            <Text style={styles.stepSub}>Select all that apply</Text>
            {EQUIPMENT.map((e) => (
              <TouchableOpacity
                key={e.id}
                style={[styles.optionCard, equipment.includes(e.id) && styles.optionSelected]}
                onPress={() => toggleItem(equipment, setEquipment, e.id)}
              >
                <Text style={[styles.optionText, equipment.includes(e.id) && styles.optionTextSelected]}>
                  {e.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        );
      case 3:
        return (
          <View>
            <Text style={styles.stepTitle}>Training schedule</Text>
            <Text style={styles.stepSub}>How many days per week?</Text>
            {SCHEDULE.map((s) => (
              <TouchableOpacity
                key={s.id}
                style={[styles.optionCard, schedule === s.id && styles.optionSelected]}
                onPress={() => setSchedule(s.id)}
              >
                <Text style={[styles.optionText, schedule === s.id && styles.optionTextSelected]}>
                  {s.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        );
      case 4:
        return (
          <View>
            <Text style={styles.stepTitle}>Any injuries?</Text>
            <Text style={styles.stepSub}>We'll modify exercises accordingly</Text>
            {INJURY_OPTIONS.map((i) => (
              <TouchableOpacity
                key={i.id}
                style={[styles.optionCard, injuries.includes(i.id) && styles.optionSelected]}
                onPress={() => toggleItem(injuries, setInjuries, i.id)}
              >
                <AlertCircle size={18} color={injuries.includes(i.id) ? "#818CF8" : "#64748B"} />
                <Text style={[styles.optionText, injuries.includes(i.id) && styles.optionTextSelected]}>
                  {i.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        );
    }
  };

  return (
    <View style={styles.container}>
      {/* Progress bar */}
      <View style={styles.progressRow}>
        {[0, 1, 2, 3, 4].map((i) => (
          <View key={i} style={[styles.progressDot, i <= step && styles.progressDotActive]} />
        ))}
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {renderStep()}
      </ScrollView>

      <View style={styles.navRow}>
        {step > 0 ? (
          <TouchableOpacity style={styles.navBtnSecondary} onPress={prev}>
            <ChevronLeft size={18} color="#94A3B8" />
            <Text style={styles.navBtnText}>Back</Text>
          </TouchableOpacity>
        ) : (
          <View />
        )}

        <TouchableOpacity
          style={[styles.navBtnPrimary, step === 4 && styles.navBtnComplete]}
          onPress={step === 4 ? complete : next}
        >
          <Text style={styles.navBtnText}>
            {step === 4 ? "Get Started" : "Next"}
          </Text>
          {step < 4 && <ChevronRight size={18} color="#F8FAFC" />}
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0F172A", paddingTop: 60 },
  progressRow: { flexDirection: "row", justifyContent: "center", gap: 8, marginBottom: 24 },
  progressDot: { width: 40, height: 4, borderRadius: 2, backgroundColor: "#334155" },
  progressDotActive: { backgroundColor: "#818CF8" },
  content: { flex: 1, paddingHorizontal: 20 },
  stepTitle: { color: "#F8FAFC", fontSize: 24, fontWeight: "700", marginBottom: 6 },
  stepSub: { color: "#94A3B8", fontSize: 14, marginBottom: 20 },
  optionCard: {
    flexDirection: "row", alignItems: "center", gap: 12,
    backgroundColor: "#1E293B", borderRadius: 12, padding: 16, marginBottom: 10,
    borderWidth: 2, borderColor: "transparent",
  },
  optionSelected: { borderColor: "#818CF8", backgroundColor: "#1E1B4B" },
  optionText: { color: "#CBD5E1", fontSize: 15, flex: 1 },
  optionTextSelected: { color: "#F8FAFC", fontWeight: "600" },
  optionDesc: { color: "#64748B", fontSize: 12 },
  navRow: {
    flexDirection: "row", justifyContent: "space-between", alignItems: "center",
    padding: 20, paddingBottom: 40,
  },
  navBtnPrimary: {
    flexDirection: "row", alignItems: "center", gap: 6,
    backgroundColor: "#4F46E5", borderRadius: 10, paddingHorizontal: 24, paddingVertical: 12,
  },
  navBtnComplete: { backgroundColor: "#10B981" },
  navBtnSecondary: {
    flexDirection: "row", alignItems: "center", gap: 4,
    paddingHorizontal: 16, paddingVertical: 12,
  },
  navBtnText: { color: "#F8FAFC", fontSize: 15, fontWeight: "600" },
});
