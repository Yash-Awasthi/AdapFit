import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronLeft } from 'lucide-react-native';
import { useTheme } from '../services/theme';
import { SCREEN_HEADER_TOP } from '../theme/layout';

export function ScreenHeader({ title, right }: { title: string; right?: React.ReactNode }) {
  const router = useRouter();
  const { theme } = useTheme();
  return (
    <View style={styles.header}>
      <TouchableOpacity onPress={() => router.back()} style={styles.backBtn} hitSlop={10}>
        <ChevronLeft size={22} color={theme.text} />
      </TouchableOpacity>
      <Text style={[styles.title, { color: theme.text }]} numberOfLines={1}>{title}</Text>
      <View style={styles.backBtn}>{right}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 12, paddingTop: SCREEN_HEADER_TOP, paddingBottom: 8,
  },
  backBtn: { padding: 8, width: 38 },
  title: { fontSize: 20, fontWeight: '700', flex: 1, textAlign: 'center' },
});
