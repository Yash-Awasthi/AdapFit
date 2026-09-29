import React, { useState } from 'react';
import { ActivityIndicator, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { useTheme } from '../services/theme';
import { authedFetch, setTokens } from '../services/authToken';
import { apiUrl } from '../services/config';

/** Current and new password; on success the server ends other sessions and returns a fresh pair for this one. */
export function ChangePassword() {
  const { theme } = useTheme();
  const [open, setOpen] = useState(false);
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  const submit = async () => {
    if (next !== confirm) return setMessage({ ok: false, text: 'The new passwords do not match.' });
    setBusy(true);
    setMessage(null);
    try {
      const res = await authedFetch(apiUrl('/api/v1/auth/change-password'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ old_password: current, new_password: next }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = Array.isArray(body.detail) ? body.detail.map((d: any) => d.msg ?? d).join(' ') : body.detail;
        setMessage({ ok: false, text: detail === 'Invalid credentials' ? 'Current password is wrong.' : String(detail ?? 'Could not change the password.') });
        return;
      }
      await setTokens(body.tokens);
      setCurrent(''); setNext(''); setConfirm('');
      setMessage({ ok: true, text: 'Password changed. Other devices are signed out.' });
    } catch {
      setMessage({ ok: false, text: 'No connection. Try again.' });
    } finally {
      setBusy(false);
    }
  };

  const input = {
    backgroundColor: theme.surface, color: theme.text, borderRadius: 10, padding: 12, marginBottom: 8, fontSize: 15,
  } as const;

  if (!open) {
    return (
      <TouchableOpacity accessibilityRole="button" onPress={() => setOpen(true)}
        style={{ backgroundColor: theme.surface, borderRadius: 12, padding: 14, marginBottom: 8 }}>
        <Text style={{ color: theme.text, fontSize: 14, fontWeight: '500' }}>Change password</Text>
      </TouchableOpacity>
    );
  }
  return (
    <View style={{ marginBottom: 8 }}>
      <TextInput style={input} placeholder="Current password" placeholderTextColor={theme.textMuted} secureTextEntry
        autoComplete="current-password" value={current} onChangeText={setCurrent} accessibilityLabel="Current password" />
      <TextInput style={input} placeholder="New password" placeholderTextColor={theme.textMuted} secureTextEntry
        autoComplete="new-password" value={next} onChangeText={setNext} accessibilityLabel="New password" />
      <TextInput style={input} placeholder="Repeat new password" placeholderTextColor={theme.textMuted} secureTextEntry
        autoComplete="new-password" value={confirm} onChangeText={setConfirm} accessibilityLabel="Repeat new password" />
      {!!message && (
        <Text accessibilityLiveRegion="polite" style={{ color: message.ok ? theme.success : theme.danger, marginBottom: 8 }}>
          {message.text}
        </Text>
      )}
      <TouchableOpacity accessibilityRole="button" disabled={busy || !current || !next} onPress={submit}
        style={{ backgroundColor: theme.primary, borderRadius: 10, padding: 14, alignItems: 'center', opacity: busy || !current || !next ? 0.5 : 1 }}>
        {busy ? <ActivityIndicator color="#fff" /> : <Text style={{ color: '#fff', fontWeight: '600' }}>Change password</Text>}
      </TouchableOpacity>
    </View>
  );
}
