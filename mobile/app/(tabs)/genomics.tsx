/**
 * Genomics — a fixed panel read from a 23andMe or AncestryDNA raw-data file.
 * Associations show the published odds ratio and its source, never a personal
 * risk; the APOE result stays hidden until the user asks for it.
 */
import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert, ActivityIndicator, TextInput } from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import { colors, spacing, radius } from '../../src/theme';
import { ScreenWrapper } from '../../src/components/ScreenWrapper';
import { GlassCard, SectionHeaderPremium } from '../../src/components/PremiumComponents';
import { useApis } from '../../src/hooks/useApi';
import { asArray, deleteJson, postForm, postJson } from '../../src/services/http';

interface Association { id: string; gene: string; rsid: string; genotype: string; condition: string; meaning: string; source: string; what_helps: string }
interface Trait { id: string; gene: string; trait: string; genotype: string; meaning: string }
interface Pgx { gene: string; status: string; phenotype: string | null; note: string; drugs?: string[]; action?: string }
interface Apoe { available: boolean; shown: boolean; counselling: string; genotype?: string; odds_ratio?: number; source?: string }
interface Report {
  status: string; message?: string; variants_read?: number;
  associations?: Association[]; traits?: Trait[]; pharmacogenomics?: Pgx[]; apoe?: Apoe | null;
  caveats?: string[]; next_step?: string;
}
interface DrugResult { drug: string; gene: string; message: string }

const TINT = '#8B5CF6';

export default function GenomicsScreen() {
  const { data, loading, refreshing, refresh, reload } = useApis<{ report: Report }>({ report: '/genomics/report' });
  const report = data.report;
  const ok = report?.status === 'ok';
  const [busy, setBusy] = useState(false);
  const [meds, setMeds] = useState('');
  const [drugResults, setDrugResults] = useState<DrugResult[] | null>(null);

  const upload = async () => {
    const pick = await DocumentPicker.getDocumentAsync({ type: ['text/plain', 'application/zip', '*/*'], copyToCacheDirectory: true });
    if (pick.canceled || !pick.assets?.[0]) return;
    const file = pick.assets[0];
    const form = new FormData();
    form.append('file', { uri: file.uri, name: file.name, type: file.mimeType ?? 'application/octet-stream' } as any);
    setBusy(true);
    const result = await postForm<Report>('/genomics/upload', form);
    setBusy(false);
    if (!result || result.status !== 'ok') {
      Alert.alert('Not read', result?.message ?? 'The file could not be uploaded.');
      return;
    }
    await reload();
  };

  const toggleApoe = (show: boolean) => {
    const go = async () => { await postJson('/genomics/apoe', { show }); await reload(); };
    if (!show) { go(); return; }
    Alert.alert('Show APOE result?', report?.apoe?.counselling ?? '', [
      { text: 'Not now', style: 'cancel' },
      { text: 'Show it', onPress: go },
    ]);
  };

  const checkDrugs = async () => {
    const list = meds.split(',').map((m) => m.trim()).filter(Boolean);
    if (!list.length) return;
    const out = await postJson<{ results: DrugResult[] }>('/genomics/drug-check', { medications: list });
    setDrugResults(asArray<DrugResult>(out?.results));
  };

  const erase = () => Alert.alert('Delete DNA results?', 'This removes the panel results kept from your file.', [
    { text: 'Cancel', style: 'cancel' },
    { text: 'Delete', style: 'destructive', onPress: async () => { await deleteJson('/genomics/report'); await reload(); } },
  ]);

  return (
    <ScreenWrapper title="Genomics" subtitle="What your DNA file says, with sources" gradient={[TINT, '#6366F1']}
      loading={loading} refreshing={refreshing} onRefresh={refresh}>
      <GlassCard variant="light" style={styles.card}>
        <Text style={styles.body}>
          Upload the raw data file from 23andMe or AncestryDNA (.txt or .zip). Only the variants below are kept; the file itself is discarded.
        </Text>
        <TouchableOpacity style={styles.btn} onPress={upload} disabled={busy} accessibilityRole="button">
          {busy ? <ActivityIndicator color="#fff" /> : <Text style={styles.btnText}>{ok ? 'Upload a new file' : 'Upload DNA file'}</Text>}
        </TouchableOpacity>
      </GlassCard>

      {ok && (
        <>
          <SectionHeaderPremium icon="medkit" iconColor={TINT} title="Medicines and your genes" />
          {asArray<Pgx>(report!.pharmacogenomics).map((p) => (
            <GlassCard key={p.gene} variant="light" style={styles.card}>
              <Text style={styles.name}>{p.gene}{p.phenotype ? ` · ${p.phenotype}` : ''}</Text>
              <Text style={styles.body}>{p.note}</Text>
              {p.status === 'not_in_file' && <Text style={styles.muted}>Not in your file.</Text>}
              {p.action && <Text style={styles.muted}>{p.action}</Text>}
            </GlassCard>
          ))}
          <GlassCard variant="light" style={styles.card}>
            <Text style={styles.name}>Check your medicines</Text>
            <TextInput style={styles.input} value={meds} onChangeText={setMeds} placeholder="e.g. clopidogrel, atorvastatin"
              placeholderTextColor={colors.text.muted} maxLength={500} />
            <TouchableOpacity style={styles.btn} onPress={checkDrugs} accessibilityRole="button">
              <Text style={styles.btnText}>Check</Text>
            </TouchableOpacity>
            {drugResults && (drugResults.length === 0
              ? <Text style={styles.muted}>None of these is affected by the genes read from your file.</Text>
              : drugResults.map((r) => <Text key={r.drug + r.gene} style={styles.body}>{r.drug}: {r.message}</Text>))}
          </GlassCard>

          <SectionHeaderPremium icon="stats-chart" iconColor={TINT} title="Studied associations" />
          {asArray<Association>(report!.associations).map((a) => (
            <GlassCard key={a.id} variant="light" style={styles.card}>
              <Text style={styles.name}>{a.gene} · {a.condition}</Text>
              <Text style={styles.muted}>{a.rsid} {a.genotype}</Text>
              <Text style={styles.body}>{a.meaning}</Text>
              <Text style={styles.body}>{a.what_helps}</Text>
              <Text style={styles.source}>{a.source}</Text>
            </GlassCard>
          ))}

          {report!.apoe?.available && (
            <GlassCard variant="light" style={styles.card}>
              <Text style={styles.name}>APOE and Alzheimer's disease</Text>
              {report!.apoe.shown ? (
                <>
                  <Text style={styles.body}>
                    Your APOE type is {report!.apoe.genotype}.
                    {report!.apoe.odds_ratio ? ` In studies, people with this type had about ${report!.apoe.odds_ratio}x the odds of people with e3/e3.` : ' This type was not linked to higher odds in the studies.'}
                  </Text>
                  <Text style={styles.body}>{report!.apoe.counselling}</Text>
                  <Text style={styles.source}>{report!.apoe.source}</Text>
                  <Text style={styles.link} onPress={() => toggleApoe(false)}>Hide this result</Text>
                </>
              ) : (
                <>
                  <Text style={styles.body}>This result is hidden. Nothing you do changes it, so decide first whether you want to know.</Text>
                  <Text style={styles.link} onPress={() => toggleApoe(true)}>Show my APOE result</Text>
                </>
              )}
            </GlassCard>
          )}

          <SectionHeaderPremium icon="body" iconColor={TINT} title="Traits" />
          {asArray<Trait>(report!.traits).map((t) => (
            <GlassCard key={t.id} variant="light" style={styles.card}>
              <Text style={styles.name}>{t.trait}</Text>
              <Text style={styles.muted}>{t.gene} {t.genotype}</Text>
              <Text style={styles.body}>{t.meaning}</Text>
            </GlassCard>
          ))}

          <GlassCard variant="light" style={styles.card}>
            {asArray<string>(report!.caveats).map((c) => <Text key={c} style={styles.muted}>• {c}</Text>)}
            <Text style={styles.body}>{report!.next_step}</Text>
            <Text style={[styles.link, { color: '#DC2626' }]} onPress={erase}>Delete my DNA results</Text>
          </GlassCard>
        </>
      )}
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  card: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.md },
  name: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  body: { fontSize: 13, color: colors.text.secondary, marginTop: 6, lineHeight: 18 },
  muted: { fontSize: 12, color: colors.text.muted, marginTop: 4, lineHeight: 17 },
  source: { fontSize: 11, color: colors.text.muted, marginTop: 6, fontStyle: 'italic' },
  input: { backgroundColor: colors.bg.input, borderRadius: radius.md, padding: 12, color: colors.text.primary, marginTop: spacing.sm },
  btn: { backgroundColor: TINT, borderRadius: radius.button, padding: 12, alignItems: 'center', marginTop: spacing.md },
  btnText: { color: '#FFF', fontWeight: '700' },
  link: { color: '#60A5FA', fontSize: 13, marginTop: 10 },
});
