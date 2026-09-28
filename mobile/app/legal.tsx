/** Shows one legal document (privacy policy, terms, health disclaimer) as served by the backend. */
import React, { useEffect, useState } from 'react';
import { ScrollView, Text, TouchableOpacity, View, ActivityIndicator, StyleSheet } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing } from '../src/theme';
import { getDocument } from '../src/services/privacy';

export default function LegalScreen() {
  const router = useRouter();
  const { doc } = useLocalSearchParams<{ doc?: string }>();
  const [text, setText] = useState<string | null | undefined>(undefined);

  useEffect(() => {
    getDocument(doc ?? 'privacy-policy').then(setText);
  }, [doc]);

  return (
    <View style={s.container}>
      <TouchableOpacity style={s.back} onPress={() => router.back()} accessibilityLabel="Back">
        <Ionicons name="arrow-back" size={24} color={colors.text.primary} />
      </TouchableOpacity>
      {text === undefined ? (
        <ActivityIndicator color={colors.primary} />
      ) : (
        <ScrollView contentContainerStyle={s.content}>
          {(text ?? 'Could not load the document. Check your connection.').split('\n').map((raw, i) => {
            if (/^\|[-| ]+\|$/.test(raw)) return null;
            const line = raw.startsWith('|') ? raw.split('|').map((c) => c.trim()).filter(Boolean).join('  ·  ') : raw;
            const heading = line.match(/^(#+)\s+(.*)/);
            const clean = (heading ? heading[2] : line).replace(/\*\*/g, '');
            return (
              <Text key={i} style={heading ? (heading[1].length === 1 ? s.h1 : s.h2) : s.p}>{clean}</Text>
            );
          })}
        </ScrollView>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep, paddingTop: 48 },
  back: { paddingHorizontal: spacing.lg, paddingBottom: spacing.sm },
  content: { padding: spacing.lg, paddingBottom: 80 },
  h1: { fontSize: 24, fontWeight: '800', color: colors.text.primary, marginBottom: spacing.md },
  h2: { fontSize: 17, fontWeight: '700', color: colors.text.primary, marginTop: spacing.lg, marginBottom: spacing.xs },
  p: { fontSize: 14, color: colors.text.secondary, lineHeight: 21 },
});
