import React, { useState } from 'react';
import { View, Text, ScrollView, TextInput, TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import Animated, { FadeInDown } from 'react-native-reanimated';
import * as Haptics from 'expo-haptics';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useTheme, CARD_SHADOW } from '../services/theme';
import { useDevSettings } from '../services/devSettings';
import { useFemaleFeatures } from '../services/gender';
import { useGrid } from '../theme/layout';
import { SECTIONS, type Section, type SectionItem } from '../navigation/sections';

export function useVisibleItems(items: SectionItem[]): SectionItem[] {
  const showFemale = useFemaleFeatures();
  return items.filter((i) => (!i.female || showFemale) && (!i.devOnly || __DEV__));
}

function Card({ item, index, width }: { item: SectionItem; index: number; width: number }) {
  const router = useRouter();
  const { theme } = useTheme();
  const { reduceMotion } = useDevSettings();
  return (
    <Animated.View entering={reduceMotion ? undefined : FadeInDown.duration(280).delay(30 * index)} style={{ width }}>
      <TouchableOpacity
        activeOpacity={0.85}
        onPress={() => { Haptics.selectionAsync(); router.push(item.route as any); }}
        accessibilityRole="button"
        accessibilityLabel={`${item.label}. ${item.sub}`}
        style={[styles.card, CARD_SHADOW, { backgroundColor: theme.surface, borderColor: theme.border }]}
      >
        <View style={[styles.cardIcon, { backgroundColor: `${item.color}22` }]}>
          <Ionicons name={item.icon} size={20} color={item.color} />
        </View>
        <Text style={[styles.cardLabel, { color: theme.text }]} numberOfLines={1}>{item.label}</Text>
        <Text style={[styles.cardSub, { color: theme.textMuted }]} numberOfLines={2}>{item.sub}</Text>
      </TouchableOpacity>
    </Animated.View>
  );
}

export function SectionGrid({ items }: { items: SectionItem[] }) {
  const grid = useGrid(2);
  return (
    <View style={[styles.grid, { gap: grid.gap }]}>
      {items.map((item, i) => <Card key={item.route} item={item} index={i} width={grid.cell} />)}
    </View>
  );
}

/** Shortcuts from Today into the other four sections. */
export function SectionShortcuts() {
  const router = useRouter();
  const { theme } = useTheme();
  return (
    <View style={styles.shortcuts}>
      {SECTIONS.filter((s) => s.key !== 'today').map((s) => (
        <TouchableOpacity
          key={s.key}
          accessibilityRole="button"
          accessibilityLabel={`${s.title}. ${s.blurb}`}
          onPress={() => { Haptics.selectionAsync(); router.navigate(s.tab as any); }}
          style={[styles.shortcut, { backgroundColor: theme.surface, borderColor: theme.border }]}
        >
          <Ionicons name={s.icon} size={18} color={theme.primary} />
          <Text style={[styles.shortcutText, { color: theme.text }]}>{s.title}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

export function SectionLanding({ sectionKey }: { sectionKey: Section['key'] }) {
  const section = SECTIONS.find((s) => s.key === sectionKey)!;
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();
  const [query, setQuery] = useState('');
  const visible = useVisibleItems(section.items);
  const q = query.trim().toLowerCase();
  const items = q ? visible.filter((i) => `${i.label} ${i.sub}`.toLowerCase().includes(q)) : visible;

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: theme.background }}
      contentContainerStyle={{ paddingTop: insets.top + 16, paddingHorizontal: 20, paddingBottom: 120 }}
      keyboardShouldPersistTaps="handled"
    >
      <Text style={[styles.title, { color: theme.text }]} accessibilityRole="header">{section.title}</Text>
      <Text style={[styles.blurb, { color: theme.textMuted }]}>{section.blurb}</Text>
      {section.searchable && (
        <View style={[styles.search, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Ionicons name="search" size={16} color={theme.textMuted} />
          <TextInput
            value={query}
            onChangeText={setQuery}
            placeholder={`Search ${section.title.toLowerCase()} programs`}
            placeholderTextColor={theme.textMuted}
            style={[styles.searchInput, { color: theme.text }]}
            accessibilityLabel={`Search ${section.title}`}
          />
        </View>
      )}
      <SectionGrid items={items} />
      {items.length === 0 && (
        <Text style={[styles.blurb, { color: theme.textMuted, marginTop: 16 }]}>Nothing matches "{query}".</Text>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: 28, fontWeight: '800' },
  blurb: { fontSize: 14, marginTop: 4, marginBottom: 16 },
  grid: { flexDirection: 'row', flexWrap: 'wrap' },
  // Fixed height so a one-line and a two-line subtitle keep the same card box.
  card: { height: 122, borderRadius: 16, borderWidth: 1, padding: 14, gap: 2 },
  cardIcon: { width: 36, height: 36, borderRadius: 10, alignItems: 'center', justifyContent: 'center', marginBottom: 6 },
  cardLabel: { fontSize: 14, fontWeight: '700' },
  cardSub: { fontSize: 11, lineHeight: 15 },
  search: { flexDirection: 'row', alignItems: 'center', gap: 8, borderWidth: 1, borderRadius: 12, paddingHorizontal: 12, marginBottom: 16 },
  searchInput: { flex: 1, paddingVertical: 10, fontSize: 14 },
  shortcuts: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  shortcut: { flexDirection: 'row', alignItems: 'center', gap: 6, borderWidth: 1, borderRadius: 12, paddingHorizontal: 12, paddingVertical: 10 },
  shortcutText: { fontSize: 13, fontWeight: '700' },
});
