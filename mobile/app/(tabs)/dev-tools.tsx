import React, { useState } from 'react';
import { View, Text, ScrollView, TextInput, TouchableOpacity, StyleSheet, Switch, Alert, Modal, FlatList } from 'react-native';
import { useRouter } from 'expo-router';
import { Check, Trash2, Zap, ChevronDown, X, Search } from 'lucide-react-native';
import * as Haptics from 'expo-haptics';
import { useTheme } from '../../src/services/theme';
import { useDevSettings, LlmProvider } from '../../src/services/devSettings';
import { api } from '../../src/services/api';
import { ScreenHeader } from '../../src/components';

const PROVIDERS: { id: LlmProvider; label: string; hint: string }[] = [
  { id: 'gemini', label: 'Gemini', hint: 'Google AI Studio key — free tier available' },
  { id: 'groq', label: 'Groq', hint: 'Fast Llama inference — free tier available' },
  { id: 'custom', label: 'Custom', hint: 'Any OpenAI-compatible endpoint (local LLM, proxy, etc)' },
];

function Chip({ label, active, onPress, theme }: { label: string; active: boolean; onPress: () => void; theme: any }) {
  return (
    <TouchableOpacity
      onPress={() => { Haptics.selectionAsync(); onPress(); }}
      style={[styles.chip, { backgroundColor: active ? theme.primary : theme.surface, borderColor: active ? theme.primary : theme.border }]}
    >
      <Text style={[styles.chipText, { color: active ? '#fff' : theme.textSecondary }]}>{label}</Text>
    </TouchableOpacity>
  );
}

export default function DevToolsScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const { llmOverride, setLlmOverride, reduceMotion, setReduceMotion } = useDevSettings();

  const [provider, setProvider] = useState<LlmProvider>(llmOverride?.provider || 'gemini');
  const [apiKey, setApiKey] = useState(llmOverride?.apiKey || '');
  const [model, setModel] = useState(llmOverride?.model || '');
  const [baseUrl, setBaseUrl] = useState(llmOverride?.baseUrl || '');
  const [testing, setTesting] = useState(false);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [modelPickerOpen, setModelPickerOpen] = useState(false);
  const [modelSearch, setModelSearch] = useState('');

  const inputStyle = [styles.input, { backgroundColor: theme.surface, borderColor: theme.border, color: theme.text }];

  function handleSave() {
    if (!apiKey.trim()) {
      Alert.alert('API key required', 'Enter an API key or clear it to go back to the built-in coach.');
      return;
    }
    if (provider === 'custom' && !baseUrl.trim()) {
      Alert.alert('Endpoint required', 'Custom provider needs a base URL (e.g. http://localhost:11434/v1).');
      return;
    }
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    setLlmOverride({ provider, apiKey: apiKey.trim(), model: model.trim() || undefined, baseUrl: baseUrl.trim() || undefined });
    router.back();
  }

  function handleClear() {
    Haptics.selectionAsync();
    setLlmOverride(null);
    setApiKey('');
    setModel('');
    setBaseUrl('');
  }

  function openModelPicker() {
    setModelSearch('');
    setModelPickerOpen(true);
    if (availableModels.length === 0) handleFetchModels();
  }

  async function handleFetchModels() {
    if (!apiKey.trim()) {
      Alert.alert('Nothing to fetch', 'Enter an API key first.');
      return;
    }
    if (provider === 'custom' && !baseUrl.trim()) {
      Alert.alert('Endpoint required', 'Custom provider needs a base URL first.');
      return;
    }
    setLoadingModels(true);
    setAvailableModels([]);
    try {
      let ids: string[] = [];
      if (provider === 'gemini') {
        const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey.trim()}`);
        const json = await res.json();
        if (!res.ok) throw new Error(json?.error?.message || `HTTP ${res.status}`);
        ids = (json.models || [])
          .filter((m: any) => (m.supportedGenerationMethods || []).includes('generateContent'))
          .map((m: any) => String(m.name).replace(/^models\//, ''));
      } else {
        const url = provider === 'groq' ? 'https://api.groq.com/openai/v1/models' : `${baseUrl.trim().replace(/\/$/, '')}/models`;
        const res = await fetch(url, { headers: { Authorization: `Bearer ${apiKey.trim()}` } });
        const json = await res.json();
        if (!res.ok) throw new Error(json?.error?.message || `HTTP ${res.status}`);
        ids = (json.data || []).map((m: any) => m.id).filter(Boolean);
      }
      ids.sort();
      setAvailableModels(ids);
      if (ids.length === 0) Alert.alert('No models found', 'The endpoint returned an empty list.');
    } catch (err: any) {
      Alert.alert('Could not fetch models', err?.message || String(err));
    }
    setLoadingModels(false);
  }

  async function handleTest() {
    if (!apiKey.trim()) {
      Alert.alert('Nothing to test', 'Enter an API key first.');
      return;
    }
    setTesting(true);
    try {
      const res = await api.chat('default', 'Say hello in one short sentence.', [], {
        // test call — uses the shared default user
        provider, api_key: apiKey.trim(), model: model.trim() || undefined, base_url: baseUrl.trim() || undefined,
      });
      Alert.alert('Response received', res.reply);
    } catch {
      Alert.alert('Test failed', 'Could not get a reply — check the key, model, and endpoint.');
    }
    setTesting(false);
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      <ScreenHeader
        title="Dev Tools"
        right={
          <TouchableOpacity onPress={handleSave} hitSlop={10}>
            <Check size={22} color={theme.primaryLight} />
          </TouchableOpacity>
        }
      />

      <ScrollView contentContainerStyle={styles.content}>
        <Text style={[styles.sectionLabel, { color: theme.textSecondary }]}>AI Coach — bring your own key</Text>
        <Text style={[styles.sectionHint, { color: theme.textMuted }]}>
          By default the coach uses the server's key (or a rule-based fallback if none is set). Set your own
          key here to use it instead — it's sent with each chat request and never stored on the server.
        </Text>

        <View style={styles.chipRow}>
          {PROVIDERS.map((p) => (
            <Chip key={p.id} label={p.label} active={provider === p.id} onPress={() => { setProvider(p.id); setAvailableModels([]); }} theme={theme} />
          ))}
        </View>
        <Text style={[styles.hint, { color: theme.textMuted }]}>{PROVIDERS.find((p) => p.id === provider)?.hint}</Text>

        {provider === 'custom' && (
          <View style={styles.field}>
            <Text style={[styles.fieldLabel, { color: theme.textSecondary }]}>Base URL</Text>
            <TextInput
              style={inputStyle} value={baseUrl} onChangeText={(v) => { setBaseUrl(v); setAvailableModels([]); }}
              placeholder="http://10.0.2.2:11434/v1" placeholderTextColor={theme.textMuted}
              autoCapitalize="none" autoCorrect={false} keyboardType="url"
            />
          </View>
        )}

        <View style={styles.field}>
          <Text style={[styles.fieldLabel, { color: theme.textSecondary }]}>API Key</Text>
          <TextInput
            style={inputStyle} value={apiKey} onChangeText={(v) => { setApiKey(v); setAvailableModels([]); }}
            placeholder="sk-..." placeholderTextColor={theme.textMuted}
            secureTextEntry autoCapitalize="none" autoCorrect={false}
          />
        </View>

        <View style={styles.field}>
          <Text style={[styles.fieldLabel, { color: theme.textSecondary }]}>Model (optional)</Text>
          <TouchableOpacity
            style={[inputStyle, styles.dropdownField]}
            onPress={openModelPicker}
          >
            <Text style={[styles.dropdownValue, { color: model ? theme.text : theme.textMuted }]} numberOfLines={1}>
              {model || (provider === 'gemini' ? 'gemini-2.0-flash' : provider === 'groq' ? 'llama-3.3-70b-versatile' : 'gpt-4o-mini')}
            </Text>
            <ChevronDown size={18} color={theme.textMuted} />
          </TouchableOpacity>
        </View>

        <View style={styles.buttonRow}>
          <TouchableOpacity style={[styles.testBtn, { backgroundColor: theme.surface, borderColor: theme.border }]} onPress={handleTest} disabled={testing}>
            <Zap size={16} color={theme.warning} />
            <Text style={[styles.testBtnText, { color: theme.text }]}>{testing ? 'Testing…' : 'Test connection'}</Text>
          </TouchableOpacity>
          {llmOverride && (
            <TouchableOpacity style={[styles.testBtn, { backgroundColor: theme.surface, borderColor: theme.border }]} onPress={handleClear}>
              <Trash2 size={16} color={theme.danger} />
              <Text style={[styles.testBtnText, { color: theme.danger }]}>Clear</Text>
            </TouchableOpacity>
          )}
        </View>

        <View style={[styles.divider, { backgroundColor: theme.border }]} />

        <Text style={[styles.sectionLabel, { color: theme.textSecondary }]}>Performance</Text>
        <View style={[styles.switchRow, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <View style={{ flex: 1 }}>
            <Text style={[styles.fieldLabel, { color: theme.text, marginBottom: 2 }]}>Reduce motion</Text>
            <Text style={[styles.hint, { color: theme.textMuted, marginTop: 0 }]}>Turns off entrance and press animations app-wide.</Text>
          </View>
          <Switch
            value={reduceMotion}
            onValueChange={(v) => { Haptics.selectionAsync(); setReduceMotion(v); }}
            trackColor={{ false: theme.border, true: theme.primary }}
            thumbColor="#fff"
          />
        </View>
      </ScrollView>

      <Modal visible={modelPickerOpen} animationType="slide" transparent onRequestClose={() => setModelPickerOpen(false)}>
        <View style={styles.modalBackdrop}>
          <View style={[styles.modalSheet, { backgroundColor: theme.background }]}>
            <View style={styles.modalHeader}>
              <Text style={[styles.modalTitle, { color: theme.text }]}>Choose a model</Text>
              <TouchableOpacity onPress={() => setModelPickerOpen(false)} hitSlop={10}>
                <X size={22} color={theme.textMuted} />
              </TouchableOpacity>
            </View>

            <View style={[styles.searchRow, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              <Search size={16} color={theme.textMuted} />
              <TextInput
                style={[styles.searchInput, { color: theme.text }]}
                value={modelSearch}
                onChangeText={setModelSearch}
                placeholder="Search or type a model name"
                placeholderTextColor={theme.textMuted}
                autoCapitalize="none"
                autoCorrect={false}
                autoFocus
              />
            </View>

            {loadingModels ? (
              <Text style={[styles.modalHint, { color: theme.textMuted }]}>Loading models…</Text>
            ) : availableModels.length === 0 ? (
              <Text style={[styles.modalHint, { color: theme.textMuted }]}>
                Couldn't load a model list. Type a model name above and use it directly.
              </Text>
            ) : null}

            <FlatList
              data={availableModels.filter((m) => m.toLowerCase().includes(modelSearch.trim().toLowerCase()))}
              keyExtractor={(m) => m}
              keyboardShouldPersistTaps="handled"
              ListHeaderComponent={
                modelSearch.trim() && !availableModels.includes(modelSearch.trim()) ? (
                  <TouchableOpacity
                    style={styles.modelRow}
                    onPress={() => { setModel(modelSearch.trim()); setModelPickerOpen(false); Haptics.selectionAsync(); }}
                  >
                    <Text style={[styles.modelRowText, { color: theme.primaryLight }]}>
                      Use "{modelSearch.trim()}"
                    </Text>
                  </TouchableOpacity>
                ) : null
              }
              renderItem={({ item }) => (
                <TouchableOpacity
                  style={styles.modelRow}
                  onPress={() => { setModel(item); setModelPickerOpen(false); Haptics.selectionAsync(); }}
                >
                  <Text style={[styles.modelRowText, { color: item === model ? theme.primaryLight : theme.text }]} numberOfLines={1}>
                    {item}
                  </Text>
                  {item === model && <Check size={16} color={theme.primaryLight} />}
                </TouchableOpacity>
              )}
              style={styles.modelList}
            />
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 20, paddingBottom: 100 },
  sectionLabel: { fontSize: 13, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8 },
  sectionHint: { fontSize: 12, lineHeight: 17, marginBottom: 16 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 8 },
  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, borderWidth: 1 },
  chipText: { fontSize: 13, fontWeight: '600' },
  hint: { fontSize: 12, marginTop: 4, marginBottom: 16 },
  field: { marginBottom: 16 },
  fieldLabel: { fontSize: 13, fontWeight: '600', marginBottom: 8 },
  input: { borderRadius: 12, borderWidth: 1, padding: 14, fontSize: 15 },
  dropdownField: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  dropdownValue: { fontSize: 15, flex: 1, marginRight: 8 },
  modalBackdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.4)', justifyContent: 'flex-end' },
  modalSheet: { borderTopLeftRadius: 20, borderTopRightRadius: 20, maxHeight: '75%', padding: 20 },
  modalHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 },
  modalTitle: { fontSize: 18, fontWeight: '700' },
  searchRow: { flexDirection: 'row', alignItems: 'center', gap: 8, borderRadius: 12, borderWidth: 1, paddingHorizontal: 14, paddingVertical: 10, marginBottom: 8 },
  searchInput: { flex: 1, fontSize: 15, padding: 0 },
  modalHint: { fontSize: 13, textAlign: 'center', paddingVertical: 20 },
  modelList: { marginTop: 4 },
  modelRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 14, paddingHorizontal: 4 },
  modelRowText: { fontSize: 15, flex: 1, marginRight: 8 },
  buttonRow: { flexDirection: 'row', gap: 10, marginTop: 4 },
  testBtn: { flexDirection: 'row', alignItems: 'center', gap: 8, borderRadius: 12, borderWidth: 1, paddingVertical: 12, paddingHorizontal: 16, flex: 1, justifyContent: 'center' },
  testBtnText: { fontSize: 13, fontWeight: '600' },
  divider: { height: 1, marginVertical: 24 },
  switchRow: { flexDirection: 'row', alignItems: 'center', borderRadius: 12, borderWidth: 1, padding: 14, gap: 12 },
});
