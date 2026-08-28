import React, { useEffect, useState } from "react";
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, Alert, AccessibilityInfo,
} from "react-native";
import {
  Heart, Pill, AlertTriangle, Activity, Mic, MicOff, ChevronRight,
  Shield, Stethoscope, Calendar,
} from "lucide-react-native";
import { useTheme } from "../../src/services/theme";
import { API_BASE_URL } from "../../src/services/config";
import { useAudioRecorder, RecordingPresets, requestRecordingPermissionsAsync } from "expo-audio";
import { File } from "expo-file-system";
import { api } from "../../src/services/api";
import { useUserStore } from "../../src/stores";

const API = API_BASE_URL;

interface Condition {
  condition_id: string;
  severity: number;
  is_active: boolean;
  notes: string;
}

interface Medication {
  name: string;
  dosage: string;
  frequency: string;
  time_of_day: string[];
  interacts_with_exercise: boolean;
  exercise_notes: string;
}

interface Restrictions {
  avoid: string[];
  modify: Record<string, any>;
  recommend: string[];
  warnings: string[];
}

interface ProfileSummary {
  active_conditions: number;
  active_medications: number;
  risk_level: string;
  conditions: string[];
  medications: string[];
  needs_doctor_clearance: boolean;
}

const CONDITION_LABELS: Record<string, string> = {
  diabetes_type1: "Type 1 Diabetes", diabetes_type2: "Type 2 Diabetes",
  hypertension: "Hypertension", hypotension: "Hypotension",
  heart_disease: "Heart Disease", asthma: "Asthma", copd: "COPD",
  thyroid_hyper: "Hyperthyroidism", thyroid_hypo: "Hypothyroidism",
  liver_disease: "Liver Disease", liver_fatty: "Fatty Liver",
  hernia_disc: "Disc Herniation", hernia_inguinal: "Inguinal Hernia",
  arthritis_osteo: "Osteoarthritis", arthritis_rheumatoid: "Rheumatoid Arthritis",
  fibromyalgia: "Fibromyalgia", sleep_apnea: "Sleep Apnea",
  depression: "Depression", anxiety_disorder: "Anxiety Disorder",
  scoliosis: "Scoliosis", osteoporosis: "Osteoporosis",
  kidney_disease: "Kidney Disease", crohns: "Crohn's Disease",
  pcos: "PCOS", migraine_chronic: "Chronic Migraine",
};

export default function HealthScreen() {
  const { theme } = useTheme();
  const s = makeStyles(theme);
  const userId = useUserStore((st) => st.userId);
  const [profile, setProfile] = useState<ProfileSummary | null>(null);
  const [conditions, setConditions] = useState<Condition[]>([]);
  const [medications, setMedications] = useState<Medication[]>([]);
  const [restrictions, setRestrictions] = useState<Restrictions | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [voiceText, setVoiceText] = useState("");
  const recorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const [showAddCondition, setShowAddCondition] = useState(false);
  const [showAddMed, setShowAddMed] = useState(false);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [prof, conds, meds, restricts] = await Promise.all([
        fetch(`${API}/api/v1/health/profile-summary?user_id=${userId}`).then(r => r.json()),
        fetch(`${API}/api/v1/health/conditions?user_id=${userId}`).then(r => r.json()),
        fetch(`${API}/api/v1/health/medications?user_id=${userId}`).then(r => r.json()),
        fetch(`${API}/api/v1/health/exercise-restrictions?user_id=${userId}`).then(r => r.json()),
      ]);
      setProfile(prof);
      setConditions(conds.conditions || []);
      setMedications(meds.medications || []);
      setRestrictions(restricts);
    } catch {}
  };

  const toggleVoice = async () => {
    if (isListening) {
      setIsListening(false);
      try {
        await recorder.stop();
        const uri = recorder.uri;
        if (uri) {
          const b64 = await new File(uri).base64();
          const stt = await api.transcribeAudio(b64, userId);
          if (stt?.text?.trim()) setVoiceText(stt.text.trim());
        }
      } catch {
        AccessibilityInfo.announceForAccessibility("Could not transcribe — type instead.");
      }
    } else {
      const perm = await requestRecordingPermissionsAsync();
      if (!perm.granted) {
        AccessibilityInfo.announceForAccessibility("Microphone permission is required for voice input.");
        return;
      }
      setIsListening(true);
      AccessibilityInfo.announceForAccessibility("Voice input activated. Say your symptom or question.");
      try {
        await recorder.prepareToRecordAsync();
        recorder.record();
      } catch {
        setIsListening(false);
      }
    }
  };

  const addCondition = async (conditionId: string) => {
    try {
      const res = await fetch(`${API}/api/v1/health/conditions?user_id=${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ condition_id: conditionId, severity: 5, is_active: true }),
      });
      if (res.ok) {
        setShowAddCondition(false);
        loadData();
      } else {
        const detail = await res.text().catch(() => "");
        Alert.alert("Could not add condition", `Server returned ${res.status}.${detail ? ` ${detail.slice(0, 200)}` : ""}`);
      }
    } catch (err: any) {
      Alert.alert("Could not reach the server", err?.message || String(err));
    }
  };

  const addMedication = async (name: string, dosage: string) => {
    try {
      const res = await fetch(`${API}/api/v1/health/medications?user_id=${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, dosage, frequency: "daily", category: "other", time_of_day: ["morning"] }),
      });
      if (res.ok) {
        setShowAddMed(false);
        loadData();
      } else {
        const detail = await res.text().catch(() => "");
        Alert.alert("Could not add medication", `Server returned ${res.status}.${detail ? ` ${detail.slice(0, 200)}` : ""}`);
      }
    } catch (err: any) {
      Alert.alert("Could not reach the server", err?.message || String(err));
    }
  };

  const riskColor = profile?.risk_level === "high" ? theme.danger : profile?.risk_level === "moderate" ? theme.warning : theme.success;

  return (
    <View style={s.container}>
      {/* Voice Input Bar */}
      <View style={s.voiceBar}>
        <TouchableOpacity
          style={[s.voiceBtn, isListening && s.voiceBtnActive]}
          onPress={toggleVoice}
          accessibilityLabel={isListening ? "Stop voice input" : "Start voice input"}
          accessibilityRole="button"
        >
          {isListening ? <MicOff size={20} color="#FFF" /> : <Mic size={20} color="#FFF" />}
        </TouchableOpacity>
        <TextInput
          style={s.voiceInput}
          placeholder="Describe symptoms or ask health question..."
          placeholderTextColor={theme.textMuted}
          value={voiceText}
          onChangeText={setVoiceText}
          accessibilityLabel="Health input field"
        />
      </View>

      <ScrollView style={s.scroll} contentContainerStyle={{ paddingBottom: 100 }} showsVerticalScrollIndicator={false}>
        {/* Risk Banner */}
        {profile?.needs_doctor_clearance && (
          <View style={[s.banner, { backgroundColor: "#7F1D1D" }]}>
            <AlertTriangle size={18} color="#FCA5A5" />
            <Text style={s.bannerText}>
              High risk profile — consult your doctor before new exercises
            </Text>
          </View>
        )}

        {/* Profile Summary Cards */}
        <View style={s.cardRow}>
          <View style={[s.summaryCard, { borderLeftColor: theme.danger }]}>
            <Text style={s.summaryNum}>{profile?.active_conditions || 0}</Text>
            <Text style={s.summaryLabel}>Conditions</Text>
          </View>
          <View style={[s.summaryCard, { borderLeftColor: "#8B5CF6" }]}>
            <Text style={s.summaryNum}>{profile?.active_medications || 0}</Text>
            <Text style={s.summaryLabel}>Medications</Text>
          </View>
          <View style={[s.summaryCard, { borderLeftColor: riskColor }]}>
            <Text style={[s.summaryNum, { color: riskColor }]}>
              {(profile?.risk_level || "low").toUpperCase()}
            </Text>
            <Text style={s.summaryLabel}>Risk Level</Text>
          </View>
        </View>

        {/* Active Conditions */}
        <View style={s.section}>
          <View style={s.sectionHeader}>
            <Stethoscope size={18} color={theme.primaryLight} />
            <Text style={s.sectionTitle}>Active Conditions</Text>
            <TouchableOpacity onPress={() => setShowAddCondition(true)} accessibilityLabel="Add condition">
              <Text style={s.addBtn}>+ Add</Text>
            </TouchableOpacity>
          </View>
          {conditions.length === 0 ? (
            <Text style={s.emptyText}>No conditions logged</Text>
          ) : (
            conditions.map((c, i) => (
              <View key={i} style={s.conditionCard}>
                <View style={s.conditionDot} />
                <View style={{ flex: 1 }}>
                  <Text style={s.conditionName}>
                    {CONDITION_LABELS[c.condition_id] || c.condition_id}
                  </Text>
                  <Text style={s.conditionMeta}>
                    Severity: {c.severity}/10 {c.notes ? `• ${c.notes}` : ""}
                  </Text>
                </View>
              </View>
            ))
          )}
        </View>

        {/* Medications */}
        <View style={s.section}>
          <View style={s.sectionHeader}>
            <Pill size={18} color="#8B5CF6" />
            <Text style={s.sectionTitle}>Current Medications</Text>
            <TouchableOpacity onPress={() => setShowAddMed(true)} accessibilityLabel="Add medication">
              <Text style={s.addBtn}>+ Add</Text>
            </TouchableOpacity>
          </View>
          {medications.length === 0 ? (
            <Text style={s.emptyText}>No medications logged</Text>
          ) : (
            medications.map((m, i) => (
              <View key={i} style={s.medCard}>
                <View style={{ flex: 1 }}>
                  <Text style={s.medName}>{m.name}</Text>
                  <Text style={s.medDetail}>
                    {m.dosage} • {m.frequency} • {m.time_of_day.join(", ")}
                  </Text>
                  {m.interacts_with_exercise && (
                    <View style={s.warningBadge}>
                      <AlertTriangle size={12} color={theme.warning} />
                      <Text style={s.warningText}>Exercise caution: {m.exercise_notes}</Text>
                    </View>
                  )}
                </View>
              </View>
            ))
          )}
        </View>

        {/* Exercise Restrictions */}
        {restrictions && (
          <View style={s.section}>
            <View style={s.sectionHeader}>
              <Shield size={18} color={theme.success} />
              <Text style={s.sectionTitle}>Exercise Restrictions</Text>
            </View>

            {restrictions.avoid.length > 0 && (
              <View style={s.restrictionGroup}>
                <Text style={s.restrictionLabel}>AVOID</Text>
                {restrictions.avoid.map((a, i) => (
                  <Text key={i} style={s.restrictionItem}>• {a.replace(/_/g, " ")}</Text>
                ))}
              </View>
            )}

            {restrictions.recommend.length > 0 && (
              <View style={s.restrictionGroup}>
                <Text style={[s.restrictionLabel, { color: theme.success }]}>RECOMMENDED</Text>
                {restrictions.recommend.map((r, i) => (
                  <Text key={i} style={[s.restrictionItem, { color: "#6EE7B7" }]}>
                    • {r.replace(/_/g, " ")}
                  </Text>
                ))}
              </View>
            )}

            {restrictions.warnings.length > 0 && (
              <View style={s.restrictionGroup}>
                <Text style={[s.restrictionLabel, { color: theme.warning }]}>WARNINGS</Text>
                {restrictions.warnings.map((w, i) => (
                  <Text key={i} style={[s.restrictionItem, { color: "#FDE68A" }]}>• {w}</Text>
                ))}
              </View>
            )}
          </View>
        )}
      </ScrollView>

      {/* Add Condition Modal */}
      {showAddCondition && (
        <View style={s.modal}>
          <View style={s.modalContent}>
            <Text style={s.modalTitle}>Add Condition</Text>
            <ScrollView style={{ maxHeight: 300 }}>
              {Object.entries(CONDITION_LABELS).map(([id, label]) => (
                <TouchableOpacity key={id} style={s.modalOption} onPress={() => addCondition(id)}>
                  <Text style={s.modalOptionText}>{label}</Text>
                  <ChevronRight size={16} color={theme.textMuted} />
                </TouchableOpacity>
              ))}
            </ScrollView>
            <TouchableOpacity style={s.modalCancel} onPress={() => setShowAddCondition(false)}>
              <Text style={s.modalCancelText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Add Medication Modal */}
      {showAddMed && (
        <View style={s.modal}>
          <View style={s.modalContent}>
            <Text style={s.modalTitle}>Add Medication</Text>
            <TextInput
              style={s.modalInput}
              placeholder="Medication name"
              placeholderTextColor={theme.textMuted}
              id="med-name"
            />
            <TextInput
              style={s.modalInput}
              placeholder="Dosage (e.g. 500mg)"
              placeholderTextColor={theme.textMuted}
              id="med-dosage"
            />
            <TouchableOpacity style={s.modalSave} onPress={() => addMedication("Medication", "500mg")}>
              <Text style={s.modalSaveText}>Save</Text>
            </TouchableOpacity>
            <TouchableOpacity style={s.modalCancel} onPress={() => setShowAddMed(false)}>
              <Text style={s.modalCancelText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.background },
    voiceBar: {
      flexDirection: "row", alignItems: "center", gap: 10,
      paddingHorizontal: 16, paddingVertical: 10, backgroundColor: theme.surface,
      borderBottomWidth: 1, borderBottomColor: theme.border,
    },
    voiceBtn: {
      width: 40, height: 40, borderRadius: 20, backgroundColor: theme.primary,
      alignItems: "center", justifyContent: "center",
    },
    voiceBtnActive: { backgroundColor: theme.danger },
    voiceInput: { flex: 1, color: theme.text, fontSize: 14, padding: 8 },
    scroll: { flex: 1, padding: 16 },
    banner: {
      flexDirection: "row", alignItems: "center", gap: 10,
      padding: 12, borderRadius: 10, marginBottom: 16,
    },
    bannerText: { color: "#FCA5A5", fontSize: 13, flex: 1 },
    cardRow: { flexDirection: "row", gap: 8, marginBottom: 20 },
    summaryCard: {
      flex: 1, backgroundColor: theme.surface, borderRadius: 10, padding: 12,
      borderLeftWidth: 3,
    },
    summaryNum: { color: theme.text, fontSize: 22, fontWeight: "700" },
    summaryLabel: { color: theme.textSecondary, fontSize: 11, marginTop: 2 },
    section: { marginBottom: 20 },
    sectionHeader: {
      flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 10,
    },
    sectionTitle: { color: theme.text, fontSize: 16, fontWeight: "600", flex: 1 },
    addBtn: { color: theme.primaryLight, fontSize: 13, fontWeight: "600" },
    emptyText: { color: theme.textMuted, fontSize: 13, fontStyle: "italic" },
    conditionCard: {
      flexDirection: "row", alignItems: "center", gap: 10,
      backgroundColor: theme.surface, borderRadius: 8, padding: 12, marginBottom: 6,
    },
    conditionDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: theme.danger },
    conditionName: { color: theme.text, fontSize: 14, fontWeight: "500" },
    conditionMeta: { color: theme.textSecondary, fontSize: 12, marginTop: 2 },
    medCard: {
      flexDirection: "row", alignItems: "center",
      backgroundColor: theme.surface, borderRadius: 8, padding: 12, marginBottom: 6,
    },
    medName: { color: theme.text, fontSize: 14, fontWeight: "500" },
    medDetail: { color: theme.textSecondary, fontSize: 12, marginTop: 2 },
    warningBadge: {
      flexDirection: "row", alignItems: "center", gap: 4,
      backgroundColor: "#78350F", borderRadius: 6, paddingHorizontal: 8, paddingVertical: 4,
      marginTop: 6, alignSelf: "flex-start",
    },
    warningText: { color: theme.warning, fontSize: 11 },
    restrictionGroup: { marginBottom: 12 },
    restrictionLabel: { color: theme.danger, fontSize: 12, fontWeight: "700", marginBottom: 4 },
    restrictionItem: { color: "#CBD5E1", fontSize: 13, marginLeft: 8, marginBottom: 2 },
    modal: {
      position: "absolute", top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: "rgba(0,0,0,0.7)", justifyContent: "center", alignItems: "center",
    },
    modalContent: {
      backgroundColor: theme.surface, borderRadius: 12, padding: 20, width: "85%", maxHeight: "70%",
    },
    modalTitle: { color: theme.text, fontSize: 18, fontWeight: "700", marginBottom: 16 },
    modalOption: {
      flexDirection: "row", justifyContent: "space-between", alignItems: "center",
      paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: theme.border,
    },
    modalOptionText: { color: "#CBD5E1", fontSize: 14 },
    modalInput: {
      backgroundColor: theme.background, borderRadius: 8, padding: 12, color: theme.text,
      fontSize: 14, marginBottom: 10,
    },
    modalSave: { backgroundColor: theme.primary, borderRadius: 8, padding: 12, alignItems: "center", marginTop: 8 },
    modalSaveText: { color: theme.text, fontWeight: "600" },
    modalCancel: { padding: 12, alignItems: "center", marginTop: 8 },
    modalCancelText: { color: theme.textSecondary },
  });
}
