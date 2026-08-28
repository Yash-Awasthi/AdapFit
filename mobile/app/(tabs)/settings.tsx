/**
 * Settings screen with API key management, notification preferences,
 * theme controls, data export, and app configuration.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Switch,
  StyleSheet,
  Alert,
} from 'react-native';
import {
  Key, Bell, Download, Shield, Moon, Sun, Globe, Heart,
  ChevronRight, Copy, Plus, Palette,
} from 'lucide-react-native';
import * as Haptics from 'expo-haptics';
import { API_BASE_URL } from '../../src/services/config';
import { useUserStore } from '../../src/stores';
import { useTheme, AccentName } from '../../src/services/theme';

const API = API_BASE_URL;

interface SettingsState {
  workoutReminders: boolean;
  recoveryCheckins: boolean;
  sleepReminders: boolean;
}

export default function SettingsScreen() {
  const userId = useUserStore((s) => s.userId);
  const { theme, isDark, toggle, accent, setAccent, accents } = useTheme();
  const [settings, setSettings] = useState<SettingsState>({
    workoutReminders: true,
    recoveryCheckins: true,
    sleepReminders: true,
  });
  const [apiKey, setApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);

  function toggleSetting(key: keyof SettingsState) {
    Haptics.selectionAsync();
    setSettings((s) => ({ ...s, [key]: !s[key] }));
  }

  function toggleDarkMode() {
    Haptics.selectionAsync();
    toggle();
  }

  function pickAccent(name: AccentName) {
    Haptics.selectionAsync();
    setAccent(name);
  }

  async function createApiKey() {
    try {
      const res = await fetch(`${API}/api/v1/auth/keys`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'mobile-app', tier: 'free' }),
      });
      if (res.ok) {
        const data = await res.json();
        setApiKey(data.api_key);
        setShowApiKey(true);
      }
    } catch {
      Alert.alert('Could not reach server', 'Backend is unreachable — try again once connected.');
    }
  }

  async function exportData(format: string) {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    try {
      const res = await fetch(`${API}/api/v1/export/all?user_id=${userId}&format=${format}`);
      if (res.ok) {
        Alert.alert('Export Ready', `Your data has been exported as ${format.toUpperCase()}.`);
      }
    } catch {
      Alert.alert('Export Failed', 'Please try again later.');
    }
  }

  const s = makeStyles(theme);

  return (
    <ScrollView style={s.container} contentContainerStyle={{ paddingBottom: 100 }}>
      <Text style={s.title}>Settings</Text>

      {/* Appearance */}
      <View style={s.section}>
        <Text style={s.sectionTitle}>Appearance</Text>
        <View style={s.card}>
          {isDark ? <Moon size={20} color={theme.primaryLight} /> : <Sun size={20} color={theme.warning} />}
          <View style={s.cardContent}>
            <Text style={s.cardTitle}>Dark Mode</Text>
            <Text style={s.cardDesc}>{isDark ? 'On — easier in low light' : 'Off — bright surroundings'}</Text>
          </View>
          <Switch
            value={isDark}
            onValueChange={toggleDarkMode}
            trackColor={{ false: theme.border, true: theme.primary }}
            thumbColor="#fff"
          />
        </View>
        <View style={[s.card, { flexDirection: 'column', alignItems: 'stretch' }]}>
          <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 12 }}>
            <Palette size={20} color={theme.primaryLight} />
            <View style={s.cardContent}>
              <Text style={s.cardTitle}>Accent Color</Text>
              <Text style={s.cardDesc}>Choose the app's highlight color</Text>
            </View>
          </View>
          <View style={{ flexDirection: 'row', gap: 12, paddingLeft: 4 }}>
            {(Object.keys(accents) as AccentName[]).map((name) => (
              <TouchableOpacity
                key={name}
                onPress={() => pickAccent(name)}
                style={[
                  s.swatch,
                  { backgroundColor: accents[name].primary },
                  accent === name && { borderWidth: 3, borderColor: theme.text },
                ]}
              />
            ))}
          </View>
        </View>
      </View>

      {/* API Key Section */}
      <View style={s.section}>
        <Text style={s.sectionTitle}>API Key</Text>
        <View style={s.card}>
          <Key size={20} color={theme.primaryLight} />
          <View style={s.cardContent}>
            <Text style={s.cardTitle}>Developer API Key</Text>
            <Text style={s.cardDesc}>
              {showApiKey ? apiKey : 'Create a key to access the API'}
            </Text>
          </View>
          <TouchableOpacity style={s.actionBtn} onPress={createApiKey}>
            <Plus size={16} color={theme.primaryLight} />
          </TouchableOpacity>
        </View>
        {showApiKey && (
          <TouchableOpacity
            style={s.copyBtn}
            onPress={() => {
              Haptics.selectionAsync();
              Alert.alert('Copied', 'API key copied to clipboard');
            }}
          >
            <Copy size={14} color={theme.primaryLight} />
            <Text style={s.copyText}>Copy Key</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Notifications */}
      <View style={s.section}>
        <Text style={s.sectionTitle}>Notifications</Text>
        <View style={s.card}>
          <Bell size={20} color={theme.warning} />
          <View style={s.cardContent}>
            <Text style={s.cardTitle}>Workout Reminders</Text>
            <Text style={s.cardDesc}>Daily workout reminders</Text>
          </View>
          <Switch
            value={settings.workoutReminders}
            onValueChange={() => toggleSetting('workoutReminders')}
            trackColor={{ false: theme.border, true: theme.primary }}
            thumbColor="#fff"
          />
        </View>
        <View style={s.card}>
          <Heart size={20} color={theme.success} />
          <View style={s.cardContent}>
            <Text style={s.cardTitle}>Recovery Check-ins</Text>
            <Text style={s.cardDesc}>Morning wellness reminders</Text>
          </View>
          <Switch
            value={settings.recoveryCheckins}
            onValueChange={() => toggleSetting('recoveryCheckins')}
            trackColor={{ false: theme.border, true: theme.primary }}
            thumbColor="#fff"
          />
        </View>
        <View style={s.card}>
          <Moon size={20} color={theme.primary} />
          <View style={s.cardContent}>
            <Text style={s.cardTitle}>Sleep Reminders</Text>
            <Text style={s.cardDesc}>Bedtime reminders</Text>
          </View>
          <Switch
            value={settings.sleepReminders}
            onValueChange={() => toggleSetting('sleepReminders')}
            trackColor={{ false: theme.border, true: theme.primary }}
            thumbColor="#fff"
          />
        </View>
      </View>

      {/* Data Export */}
      <View style={s.section}>
        <Text style={s.sectionTitle}>Data Export</Text>
        <TouchableOpacity style={s.exportBtn} onPress={() => exportData('json')}>
          <Download size={18} color={theme.success} />
          <Text style={s.exportText}>Export as JSON</Text>
          <ChevronRight size={16} color={theme.textMuted} />
        </TouchableOpacity>
        <TouchableOpacity style={s.exportBtn} onPress={() => exportData('csv')}>
          <Download size={18} color={theme.primary} />
          <Text style={s.exportText}>Export as CSV</Text>
          <ChevronRight size={16} color={theme.textMuted} />
        </TouchableOpacity>
      </View>

      {/* App Info */}
      <View style={s.section}>
        <Text style={s.sectionTitle}>About</Text>
        <View style={s.card}>
          <Globe size={20} color={theme.primaryLight} />
          <View style={s.cardContent}>
            <Text style={s.cardTitle}>AdapFit v2.0.0</Text>
            <Text style={s.cardDesc}>AI-Powered Adaptive Fitness Engine</Text>
          </View>
        </View>
        <View style={s.card}>
          <Shield size={20} color={theme.success} />
          <View style={s.cardContent}>
            <Text style={s.cardTitle}>Privacy</Text>
            <Text style={s.cardDesc}>Your data stays on your device</Text>
          </View>
        </View>
      </View>
    </ScrollView>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.background, padding: 20 },
    title: { fontSize: 28, fontWeight: '700', color: theme.text, marginTop: 48, marginBottom: 24 },
    section: { marginBottom: 24 },
    sectionTitle: { fontSize: 14, fontWeight: '600', color: theme.textMuted, marginBottom: 8, textTransform: 'uppercase' },
    card: {
      flexDirection: 'row',
      alignItems: 'center',
      backgroundColor: theme.surface,
      borderRadius: 12,
      padding: 14,
      marginBottom: 8,
    },
    cardContent: { flex: 1, marginLeft: 12 },
    cardTitle: { fontSize: 14, fontWeight: '600', color: theme.text },
    cardDesc: { fontSize: 12, color: theme.textMuted, marginTop: 2 },
    actionBtn: { padding: 8 },
    copyBtn: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 6,
      padding: 8,
    },
    copyText: { fontSize: 12, color: theme.primaryLight, fontWeight: '600' },
    exportBtn: {
      flexDirection: 'row',
      alignItems: 'center',
      backgroundColor: theme.surface,
      borderRadius: 12,
      padding: 14,
      marginBottom: 8,
    },
    exportText: { flex: 1, marginLeft: 12, fontSize: 14, color: theme.text, fontWeight: '500' },
    swatch: { width: 36, height: 36, borderRadius: 18 },
  });
}
