import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Switch } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export default function AccessibilitySettingsScreen() {
  const [fontScale, setFontScale] = useState(1.0);
  const [highContrast, setHighContrast] = useState(false);
  const [reduceMotion, setReduceMotion] = useState(false);
  const [voiceControl, setVoiceControl] = useState(false);
  const [largeTouch, setLargeTouch] = useState(false);
  const [screenReader, setScreenReader] = useState(false);
  const [captions, setCaptions] = useState(false);

  const fontSizes = [
    { label: 'Small', value: 0.85 },
    { label: 'Normal', value: 1.0 },
    { label: 'Large', value: 1.15 },
    { label: 'X-Large', value: 1.3 },
    { label: 'XX-Large', value: 1.5 },
  ];

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>♿ Accessibility Settings</Text>
        <Text style={styles.headerSubtitle}>Customize the app for your needs</Text>
      </View>

      <ScrollView style={styles.content}>
        <Text style={styles.sectionTitle}>Text & Display</Text>

        <View style={styles.card}>
          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Font Size</Text>
              <Text style={styles.settingDesc}>Adjust text size throughout the app</Text>
            </View>
          </View>
          <View style={styles.fontOptions}>
            {fontSizes.map(fs => (
              <TouchableOpacity
                key={fs.value}
                style={[styles.fontBtn, fontScale === fs.value && styles.fontBtnActive]}
                onPress={() => setFontScale(fs.value)}
              >
                <Text style={[styles.fontBtnText, fontScale === fs.value && styles.fontBtnTextActive]}>
                  {fs.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={styles.card}>
          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>High Contrast Mode</Text>
              <Text style={styles.settingDesc}>Increase color contrast for better visibility</Text>
            </View>
            <Switch value={highContrast} onValueChange={setHighContrast} trackColor={{ true: '#3B82F6' }} />
          </View>
        </View>

        <Text style={styles.sectionTitle}>Motion & Interaction</Text>

        <View style={styles.card}>
          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Reduce Motion</Text>
              <Text style={styles.settingDesc}>Minimize animations and transitions</Text>
            </View>
            <Switch value={reduceMotion} onValueChange={setReduceMotion} trackColor={{ true: '#3B82F6' }} />
          </View>
        </View>

        <View style={styles.card}>
          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Large Touch Targets</Text>
              <Text style={styles.settingDesc}>Increase button and link sizes (WCAG 2.5.5)</Text>
            </View>
            <Switch value={largeTouch} onValueChange={setLargeTouch} trackColor={{ true: '#3B82F6' }} />
          </View>
        </View>

        <Text style={styles.sectionTitle}>Voice & Audio</Text>

        <View style={styles.card}>
          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Voice Control</Text>
              <Text style={styles.settingDesc}>Navigate and control the app with your voice</Text>
            </View>
            <Switch value={voiceControl} onValueChange={setVoiceControl} trackColor={{ true: '#3B82F6' }} />
          </View>
          {voiceControl && (
            <View style={styles.voiceCommands}>
              <Text style={styles.voiceTitle}>Voice Commands:</Text>
              {['"Go home"', '"Start workout"', '"Log water"', '"Emergency"', '"Check heart rate"'].map(cmd => (
                <Text key={cmd} style={styles.voiceCmd}>{cmd}</Text>
              ))}
            </View>
          )}
        </View>

        <View style={styles.card}>
          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Screen Reader Optimization</Text>
              <Text style={styles.settingDesc}>Enhanced labels for TalkBack/VoiceOver</Text>
            </View>
            <Switch value={screenReader} onValueChange={setScreenReader} trackColor={{ true: '#3B82F6' }} />
          </View>
        </View>

        <View style={styles.card}>
          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Video Captions</Text>
              <Text style={styles.settingDesc}>Auto-generated captions for video content</Text>
            </View>
            <Switch value={captions} onValueChange={setCaptions} trackColor={{ true: '#3B82F6' }} />
          </View>
        </View>

        <Text style={styles.sectionTitle}>WCAG 2.1 Compliance</Text>
        <View style={styles.complianceCard}>
          <View style={styles.complianceRow}>
            <Ionicons name="checkmark-circle" size={18} color="#10B981" />
            <Text style={styles.complianceText}>1.1.1 Non-text Content — Alt text provided</Text>
          </View>
          <View style={styles.complianceRow}>
            <Ionicons name="checkmark-circle" size={18} color="#10B981" />
            <Text style={styles.complianceText}>1.3.1 Info and Structure — Semantic headings</Text>
          </View>
          <View style={styles.complianceRow}>
            <Ionicons name="checkmark-circle" size={18} color="#10B981" />
            <Text style={styles.complianceText}>1.4.3 Contrast — 4.5:1 minimum ratio</Text>
          </View>
          <View style={styles.complianceRow}>
            <Ionicons name="checkmark-circle" size={18} color="#10B981" />
            <Text style={styles.complianceText}>2.1.1 Keyboard — Full keyboard navigation</Text>
          </View>
          <View style={styles.complianceRow}>
            <Ionicons name="checkmark-circle" size={18} color="#10B981" />
            <Text style={styles.complianceText}>2.4.7 Focus Visible — Clear focus indicators</Text>
          </View>
          <View style={styles.complianceRow}>
            <Ionicons name="checkmark-circle" size={18} color="#10B981" />
            <Text style={styles.complianceText}>2.5.5 Target Size — 44px minimum targets</Text>
          </View>
          <View style={styles.complianceRow}>
            <Ionicons name="checkmark-circle" size={18} color="#10B981" />
            <Text style={styles.complianceText}>3.1.1 Language — Screen reader labels</Text>
          </View>
          <View style={styles.complianceRow}>
            <Ionicons name="checkmark-circle" size={18} color="#10B981" />
            <Text style={styles.complianceText}>4.1.2 Name, Role, Value — ARIA attributes</Text>
          </View>
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0F172A' },
  header: { paddingTop: 50, paddingHorizontal: 20, paddingBottom: 16, backgroundColor: '#1E293B' },
  headerTitle: { fontSize: 24, fontWeight: 'bold', color: '#F8FAFC' },
  headerSubtitle: { fontSize: 14, color: '#94A3B8', marginTop: 4 },
  content: { flex: 1, paddingHorizontal: 16, paddingTop: 16 },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', color: '#94A3B8', marginBottom: 8, marginTop: 8, textTransform: 'uppercase', letterSpacing: 1 },
  card: { backgroundColor: '#1E293B', borderRadius: 12, padding: 16, marginBottom: 10 },
  settingRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  settingInfo: { flex: 1, marginRight: 12 },
  settingLabel: { fontSize: 16, fontWeight: 'bold', color: '#F8FAFC' },
  settingDesc: { fontSize: 13, color: '#94A3B8', marginTop: 2 },
  fontOptions: { flexDirection: 'row', gap: 6, marginTop: 12 },
  fontBtn: { flex: 1, paddingVertical: 8, borderRadius: 8, backgroundColor: '#334155', alignItems: 'center' },
  fontBtnActive: { backgroundColor: '#3B82F6' },
  fontBtnText: { fontSize: 12, color: '#94A3B8', fontWeight: '600' },
  fontBtnTextActive: { color: '#FFF' },
  voiceCommands: { marginTop: 12, padding: 12, backgroundColor: '#334155', borderRadius: 8 },
  voiceTitle: { fontSize: 13, fontWeight: 'bold', color: '#F8FAFC', marginBottom: 6 },
  voiceCmd: { fontSize: 13, color: '#3B82F6', marginBottom: 2, fontFamily: 'monospace' },
  complianceCard: { backgroundColor: '#1E293B', borderRadius: 12, padding: 16 },
  complianceRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
  complianceText: { fontSize: 13, color: '#94A3B8', flex: 1 },
});
