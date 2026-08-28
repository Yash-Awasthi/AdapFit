import React, { useState } from "react";
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView, Dimensions
} from "react-native";
import { useRouter } from "expo-router";
import {
  Target, Dumbbell, Calendar, AlertCircle, ChevronRight, ChevronLeft,
  Zap, Moon, Heart, Activity
} from "lucide-react-native";
import { useTheme } from "../src/services/theme";
import { useUserStore } from "../src/stores";
import AsyncStorage from "@react-native-async-storage/async-storage";

const GOAL_TO_BACKEND: Record<string, string> = {
  strength: "strength",
  hypertrophy: "hypertrophy",
  fat_loss: "fat_loss",
  endurance: "endurance",
  recovery: "general_fitness",
  general: "general_fitness",
};

const EXPERIENCE_TO_BACKEND: Record<string, string> = {
  beginner: "beginner",
  intermediate: "intermediate",
  advanced: "advanced",
  elite: "advanced",
};

const EQUIPMENT_TO_BACKEND: Record<string, string[]> = {
  full_gym: ["barbell", "dumbbells", "machines", "bodyweight"],
  home_gym: ["dumbbells", "bodyweight", "bands"],
  dumbbells_only: ["dumbbells", "bodyweight"],
  bodyweight: ["bodyweight"],
  resistance_bands: ["bands", "bodyweight"],
};

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
  const { theme } = useTheme();
  const s = makeStyles(theme);
  const updateProfile = useUserStore((st) => st.updateProfile);
  const [step, setStep] = useState(0);
  const [goals, setGoals] = useState<string[]>([]);
  const [experience, setExperience] = useState("");
  const [equipment, setEquipment] = useState<string[]>([]);
  const [schedule, setSchedule] = useState("");
  const [injuries, setInjuries] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  const toggleItem = (arr: string[], setArr: (v: string[]) => void, id: string) => {
    setArr(arr.includes(id) ? arr.filter((x) => x !== id) : [...arr, id]);
  };

  const next = () => setStep(Math.min(step + 1, 4));
  const prev = () => setStep(Math.max(step - 1, 0));

  const complete = async () => {
    setSaving(true);
    const equipmentAccess = Array.from(new Set(equipment.flatMap((id) => EQUIPMENT_TO_BACKEND[id] || [id])));
    try {
      await updateProfile({
        primary_goal: GOAL_TO_BACKEND[goals[0]] || "general_fitness",
        fitness_level: EXPERIENCE_TO_BACKEND[experience] || "intermediate",
        preferred_days_per_week: schedule ? parseInt(schedule, 10) : 4,
        equipment_access: equipmentAccess.length ? equipmentAccess : ["bodyweight"],
      });
    } catch {
      // Offline or server unreachable — the sync daemon will pick this up
      // once the profile screen re-saves it; onboarding still completes.
    }
    // No backend field for injury history yet — kept on-device and passed
    // directly to injury-risk calls that already accept it per-request.
    await AsyncStorage.setItem("@adapfit/injury_history", JSON.stringify(injuries.filter((i) => i !== "none")));
    setSaving(false);
    router.replace("/(tabs)");
  };

  const renderStep = () => {
    switch (step) {
      case 0:
        return (
          <View>
            <Text style={s.stepTitle}>What are your goals?</Text>
            <Text style={s.stepSub}>Select one or more</Text>
            {GOALS.map((g) => {
              const Icon = g.icon;
              const sel = goals.includes(g.id);
              return (
                <TouchableOpacity
                  key={g.id}
                  style={[s.optionCard, sel && s.optionSelected]}
                  onPress={() => toggleItem(goals, setGoals, g.id)}
                >
                  <Icon size={20} color={sel ? theme.primaryLight : theme.textMuted} />
                  <Text style={[s.optionText, sel && s.optionTextSelected]}>{g.label}</Text>
                </TouchableOpacity>
              );
            })}
          </View>
        );
      case 1:
        return (
          <View>
            <Text style={s.stepTitle}>Your experience level</Text>
            <Text style={s.stepSub}>This helps us calibrate intensity</Text>
            {EXPERIENCE.map((e) => (
              <TouchableOpacity
                key={e.id}
                style={[s.optionCard, experience === e.id && s.optionSelected]}
                onPress={() => setExperience(e.id)}
              >
                <Text style={[s.optionText, experience === e.id && s.optionTextSelected]}>
                  {e.label}
                </Text>
                <Text style={s.optionDesc}>{e.desc}</Text>
              </TouchableOpacity>
            ))}
          </View>
        );
      case 2:
        return (
          <View>
            <Text style={s.stepTitle}>Equipment available</Text>
            <Text style={s.stepSub}>Select all that apply</Text>
            {EQUIPMENT.map((e) => (
              <TouchableOpacity
                key={e.id}
                style={[s.optionCard, equipment.includes(e.id) && s.optionSelected]}
                onPress={() => toggleItem(equipment, setEquipment, e.id)}
              >
                <Text style={[s.optionText, equipment.includes(e.id) && s.optionTextSelected]}>
                  {e.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        );
      case 3:
        return (
          <View>
            <Text style={s.stepTitle}>Training schedule</Text>
            <Text style={s.stepSub}>How many days per week?</Text>
            {SCHEDULE.map((sc) => (
              <TouchableOpacity
                key={sc.id}
                style={[s.optionCard, schedule === sc.id && s.optionSelected]}
                onPress={() => setSchedule(sc.id)}
              >
                <Text style={[s.optionText, schedule === sc.id && s.optionTextSelected]}>
                  {sc.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        );
      case 4:
        return (
          <View>
            <Text style={s.stepTitle}>Any injuries?</Text>
            <Text style={s.stepSub}>We'll modify exercises accordingly</Text>
            {INJURY_OPTIONS.map((i) => (
              <TouchableOpacity
                key={i.id}
                style={[s.optionCard, injuries.includes(i.id) && s.optionSelected]}
                onPress={() => toggleItem(injuries, setInjuries, i.id)}
              >
                <AlertCircle size={18} color={injuries.includes(i.id) ? theme.primaryLight : theme.textMuted} />
                <Text style={[s.optionText, injuries.includes(i.id) && s.optionTextSelected]}>
                  {i.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        );
    }
  };

  return (
    <View style={s.container}>
      {/* Progress bar */}
      <View style={s.progressRow}>
        {[0, 1, 2, 3, 4].map((i) => (
          <View key={i} style={[s.progressDot, i <= step && s.progressDotActive]} />
        ))}
      </View>

      <ScrollView style={s.content} showsVerticalScrollIndicator={false}>
        {renderStep()}
      </ScrollView>

      <View style={s.navRow}>
        {step > 0 ? (
          <TouchableOpacity style={s.navBtnSecondary} onPress={prev}>
            <ChevronLeft size={18} color={theme.textSecondary} />
            <Text style={s.navBtnText}>Back</Text>
          </TouchableOpacity>
        ) : (
          <View />
        )}

        <TouchableOpacity
          style={[s.navBtnPrimary, step === 4 && s.navBtnComplete]}
          onPress={step === 4 ? complete : next}
          disabled={saving}
        >
          <Text style={s.navBtnText}>
            {step === 4 ? (saving ? "Saving..." : "Get Started") : "Next"}
          </Text>
          {step < 4 && <ChevronRight size={18} color={theme.text} />}
        </TouchableOpacity>
      </View>
    </View>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.background, paddingTop: 60 },
    progressRow: { flexDirection: "row", justifyContent: "center", gap: 8, marginBottom: 24 },
    progressDot: { width: 40, height: 4, borderRadius: 2, backgroundColor: theme.surfaceHover },
    progressDotActive: { backgroundColor: theme.primaryLight },
    content: { flex: 1, paddingHorizontal: 20 },
    stepTitle: { color: theme.text, fontSize: 24, fontWeight: "700", marginBottom: 6 },
    stepSub: { color: theme.textSecondary, fontSize: 14, marginBottom: 20 },
    optionCard: {
      flexDirection: "row", alignItems: "center", gap: 12,
      backgroundColor: theme.surface, borderRadius: 12, padding: 16, marginBottom: 10,
      borderWidth: 2, borderColor: "transparent",
    },
    optionSelected: { borderColor: theme.primaryLight, backgroundColor: theme.primaryBg },
    optionText: { color: "#CBD5E1", fontSize: 15, flex: 1 },
    optionTextSelected: { color: theme.text, fontWeight: "600" },
    optionDesc: { color: theme.textMuted, fontSize: 12 },
    navRow: {
      flexDirection: "row", justifyContent: "space-between", alignItems: "center",
      padding: 20, paddingBottom: 40,
    },
    navBtnPrimary: {
      flexDirection: "row", alignItems: "center", gap: 6,
      backgroundColor: theme.primary, borderRadius: 10, paddingHorizontal: 24, paddingVertical: 12,
    },
    navBtnComplete: { backgroundColor: theme.success },
    navBtnSecondary: {
      flexDirection: "row", alignItems: "center", gap: 4,
      paddingHorizontal: 16, paddingVertical: 12,
    },
    navBtnText: { color: theme.text, fontSize: 15, fontWeight: "600" },
  });
}
