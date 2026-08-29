/**
 * AI Health Coach — Daily insights, Q&A, weekly report, recommendations
 */
import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, TextInput, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, radius, presets, getScoreColor } from '../../src/theme';

import { API_V1 as API } from '../../src/services/config';
const api = async (p: string, o?: RequestInit) => { try { const r = await fetch(`${API}${p}`, { headers: { 'Content-Type': 'application/json' }, ...o }); return r.ok ? await r.json() : null; } catch { return null; } };

const PRIORITY_COLORS: Record<string, string> = { high: colors.health.danger, medium: colors.health.energy, low: colors.health.calm };

export default function CoachScreen() {
  const [insight, setInsight] = useState<any>(null);
  const [report, setReport] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [motivation, setMotivation] = useState('');
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState<{role: string; text: string}[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [activeView, setActiveView] = useState<'insights' | 'chat' | 'report'>('insights');

  const load = useCallback(async () => {
    const [i, r, rec, m] = await Promise.allSettled([
      api('/ai-coach/daily-insight'), api('/ai-coach/weekly-report'),
      api('/ai-coach/recommendations'), api('/ai-coach/motivation'),
    ]);
    if (i.status === 'fulfilled') setInsight(i.value);
    if (r.status === 'fulfilled') setReport(r.value);
    if (rec.status === 'fulfilled') setRecommendations(rec.value?.recommendations || []);
    if (m.status === 'fulfilled') setMotivation(m.value?.message || '');
  }, []);

  useEffect(() => { load(); }, [load]);

  const askQuestion = async () => {
    if (!chatInput.trim()) return;
    const q = chatInput.trim();
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', text: q }]);
    setChatLoading(true);
    const r = await api('/ai-coach/ask', { method: 'POST', body: JSON.stringify({ question: q }) });
    setChatLoading(false);
    if (r?.answer) setChatMessages(prev => [...prev, { role: 'coach', text: r.answer }]);
  };

  return (
    <ScrollView style={co.container}>
      <View style={co.header}>
        <Text style={typography.heading.h1}>AI Coach</Text>
        <Text style={typography.body.sm}>Your personalized health advisor</Text>
      </View>

      {/* View Tabs */}
      <View style={co.tabRow}>
        {(['insights', 'chat', 'report'] as const).map(v => (
          <TouchableOpacity key={v} style={[co.tab, activeView === v && co.tabActive]} onPress={() => setActiveView(v)}>
            <Text style={[co.tabText, activeView === v && co.tabTextActive]}>{v.charAt(0).toUpperCase() + v.slice(1)}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Insights View */}
      {activeView === 'insights' && (
        <>
          {/* Daily Insight */}
          {insight && (
            <View style={[presets.card, { marginHorizontal: spacing.lg, borderLeftWidth: 3, borderLeftColor: PRIORITY_COLORS[insight.priority || 'medium'] }]}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginBottom: spacing.sm }}>
                <Text style={{ fontSize: 24 }}>{insight.icon}</Text>
                <View style={{ flex: 1 }}><Text style={typography.heading.h4}>{insight.title}</Text><Text style={typography.body.xs}>{insight.category}</Text></View>
              </View>
              <Text style={[typography.body.md, { marginBottom: spacing.md }]}>{insight.message}</Text>
              <View style={[co.actionBadge, { backgroundColor: PRIORITY_COLORS[insight.priority || 'medium'] + '20' }]}>
                <Ionicons name="arrow-forward" size={14} color={PRIORITY_COLORS[insight.priority || 'medium']} />
                <Text style={[typography.body.sm, { color: PRIORITY_COLORS[insight.priority || 'medium'] }]}>{insight.action}</Text>
              </View>
            </View>
          )}

          {/* Motivation */}
          {motivation && (
            <View style={[presets.card, { marginHorizontal: spacing.lg, backgroundColor: colors.primaryMuted }]}>
              <Text style={[typography.body.md, { fontStyle: 'italic', textAlign: 'center', color: colors.primaryLight }]}>{motivation}</Text>
            </View>
          )}

          {/* Recommendations */}
          <View style={[presets.card, { marginHorizontal: spacing.lg }]}>
            <Text style={[typography.heading.h4, { marginBottom: spacing.md }]}>Today's Recommendations</Text>
            {recommendations.map((rec, i) => (
              <View key={i} style={co.recCard}>
                <Text style={{ fontSize: 20 }}>{rec.icon}</Text>
                <View style={{ flex: 1 }}>
                  <Text style={typography.label.lg}>{rec.title}</Text>
                  <Text style={typography.body.sm}>{rec.message}</Text>
                </View>
                <View style={[co.priorityDot, { backgroundColor: PRIORITY_COLORS[rec.priority || 'low'] }]} />
              </View>
            ))}
          </View>
        </>
      )}

      {/* Chat View */}
      {activeView === 'chat' && (
        <>
          <View style={[presets.card, { marginHorizontal: spacing.lg, minHeight: 300 }]}>
            {chatMessages.length === 0 && (
              <View style={{ alignItems: 'center', paddingVertical: spacing['3xl'] }}>
                <Text style={{ fontSize: 48 }}></Text>
                <Text style={[typography.body.md, { marginTop: spacing.md, textAlign: 'center' }]}>Ask me anything about health, fitness, nutrition, or recovery!</Text>
              </View>
            )}
            {chatMessages.map((msg, i) => (
              <View key={i} style={[co.chatBubble, msg.role === 'user' ? co.chatUser : co.chatCoach]}>
                <Text style={[typography.body.md, { color: msg.role === 'user' ? '#FFF' : colors.text.primary }]}>{msg.text}</Text>
              </View>
            ))}
            {chatLoading && <ActivityIndicator color={colors.primary} style={{ marginTop: spacing.md }} />}
          </View>
          <View style={co.chatInputRow}>
            <TextInput style={co.chatInput} value={chatInput} onChangeText={setChatInput} placeholder="Ask about health, fitness..." placeholderTextColor={colors.text.muted} onSubmitEditing={askQuestion} />
            <TouchableOpacity style={co.sendBtn} onPress={askQuestion}><Ionicons name="send" size={18} color="#FFF" /></TouchableOpacity>
          </View>
        </>
      )}

      {/* Report View */}
      {activeView === 'report' && report && (
        <View style={[presets.card, { marginHorizontal: spacing.lg }]}>
          <Text style={[typography.heading.h4, { marginBottom: spacing.xs }]}>Weekly Report</Text>
          <Text style={[typography.body.xs, { color: colors.text.muted, marginBottom: spacing.md }]}>{report.period}</Text>
          <View style={[co.scoreCircle, { borderColor: getScoreColor(report.health_score) + '30' }]}>
            <Text style={[typography.metric.large, { color: getScoreColor(report.health_score) }]}>{report.health_score}</Text>
            <Text style={typography.body.xs}>Health Score</Text>
          </View>
          <Text style={[typography.body.md, { marginTop: spacing.lg, lineHeight: 22 }]}>{report.report}</Text>
          {report.highlights && (
            <>
              <Text style={[typography.heading.h4, { marginTop: spacing.lg, marginBottom: spacing.sm }]}>Highlights</Text>
              {report.highlights.map((h: string, i: number) => (
                <View key={i} style={{ flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.xs }}>
                  <Ionicons name="checkmark-circle" size={14} color={colors.health.calm} />
                  <Text style={typography.body.sm}>{h}</Text>
                </View>
              ))}
            </>
          )}
          {report.focus_next_week && (
            <>
              <Text style={[typography.heading.h4, { marginTop: spacing.lg, marginBottom: spacing.sm }]}>Focus Next Week</Text>
              {report.focus_next_week.map((f: string, i: number) => (
                <View key={i} style={{ flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.xs }}>
                  <Ionicons name="arrow-forward" size={14} color={colors.primary} />
                  <Text style={typography.body.sm}>{f}</Text>
                </View>
              ))}
            </>
          )}
        </View>
      )}
      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const co = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.primary },
  header: { padding: spacing.screenPadding, paddingTop: 50, paddingBottom: spacing.lg },
  tabRow: { flexDirection: 'row', marginHorizontal: spacing.lg, marginBottom: spacing.lg, backgroundColor: colors.bg.card, borderRadius: radius.md, padding: spacing.xs, borderWidth: 1, borderColor: colors.surface.border },
  tab: { flex: 1, paddingVertical: spacing.sm, alignItems: 'center', borderRadius: radius.sm - 2 },
  tabActive: { backgroundColor: colors.primary },
  tabText: { fontSize: typography.fontSize.sm, color: colors.text.muted },
  tabTextActive: { color: '#FFF' },
  actionBadge: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs, paddingHorizontal: spacing.md, paddingVertical: spacing.sm, borderRadius: radius.md },
  recCard: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.md, backgroundColor: colors.bg.input, padding: spacing.md, borderRadius: radius.md, marginBottom: spacing.sm, borderWidth: 1, borderColor: colors.surface.border },
  priorityDot: { width: 8, height: 8, borderRadius: 4, marginTop: 4 },
  chatBubble: { padding: spacing.md, borderRadius: radius.lg, marginBottom: spacing.sm, maxWidth: '85%' },
  chatUser: { backgroundColor: colors.primary, alignSelf: 'flex-end', borderBottomRightRadius: radius.xs },
  chatCoach: { backgroundColor: colors.bg.elevated, alignSelf: 'flex-start', borderBottomLeftRadius: radius.xs, borderWidth: 1, borderColor: colors.surface.border },
  chatInputRow: { flexDirection: 'row', gap: spacing.sm, paddingHorizontal: spacing.lg, marginBottom: spacing.lg },
  chatInput: { flex: 1, backgroundColor: colors.bg.card, borderRadius: radius.lg, paddingHorizontal: spacing.lg, paddingVertical: spacing.sm + 2, color: colors.text.primary, borderWidth: 1, borderColor: colors.surface.border, fontSize: typography.fontSize.base },
  sendBtn: { width: 44, height: 44, borderRadius: 22, backgroundColor: colors.primary, justifyContent: 'center', alignItems: 'center' },
  scoreCircle: { width: 100, height: 100, borderRadius: 50, borderWidth: 4, alignSelf: 'center', justifyContent: 'center', alignItems: 'center', backgroundColor: colors.bg.input },
});
