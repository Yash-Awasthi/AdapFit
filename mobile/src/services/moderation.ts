import { Alert } from 'react-native';
import { postJson } from './http';

type Target = { shareId: string; authorId: string; authorName: string; commentId?: string; userId: string };

/** Report a post or comment, or block its author; `onDone` reloads so the hidden content disappears. */
export function openModeration(t: Target, onDone: () => void) {
  const report = (reason: string) =>
    postJson(`/community/${t.shareId}/report?user_id=${t.userId}`, { reason, comment_id: t.commentId ?? null }).then((r) => {
      Alert.alert(r ? 'Reported' : 'Not sent', r ? 'Thanks. You will not see this again.' : 'Check your connection and try again.');
      onDone();
    });
  const block = () =>
    postJson(`/community/block/${t.authorId}?user_id=${t.userId}`).then((r) => {
      Alert.alert(r ? 'Blocked' : 'Not sent', r ? `You will not see posts or replies from ${t.authorName}.` : 'Check your connection and try again.');
      onDone();
    });
  const buttons = [
    {
      text: 'Report',
      onPress: () =>
        Alert.alert('Why are you reporting this?', undefined, [
          { text: 'Spam', onPress: () => report('spam') },
          { text: 'Abusive', onPress: () => report('abuse') },
          { text: 'Harmful health advice', onPress: () => report('harmful_health_advice') },
        ], { cancelable: true }),
    },
    ...(t.authorId !== t.userId ? [{ text: `Block ${t.authorName}`, style: 'destructive' as const, onPress: block }] : []),
    { text: 'Cancel', style: 'cancel' as const },
  ];
  Alert.alert(t.commentId ? 'This reply' : 'This post', undefined, buttons);
}
