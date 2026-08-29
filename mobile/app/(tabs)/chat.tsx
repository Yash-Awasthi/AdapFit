import React, { useState, useRef, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  FlatList,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
} from 'react-native';
import { Send, Bot, User, Mic, Wrench } from 'lucide-react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTabBarHeight } from '../../src/theme/layout';
import * as Haptics from 'expo-haptics';
import { api } from '../../src/services/api';
import { useTheme } from '../../src/services/theme';
import { useDevSettings } from '../../src/services/devSettings';
import { WS_BASE_URL } from '../../src/services/config';
import { useUserStore } from '../../src/stores';

const WS_URL = WS_BASE_URL;

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

// WebSocket streaming chat hook
function useStreamChat() {
  const wsRef = useRef<WebSocket | null>(null);
  const [streamingContent, setStreamingContent] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  const connect = useCallback((userId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return wsRef.current;
    const ws = new WebSocket(`${WS_URL}/api/v1/chat/ws/${userId}`);
    wsRef.current = ws;
    return ws;
  }, []);

  const sendStreaming = useCallback(
    (text: string, userId: string = 'default') => {
      return new Promise<string>((resolve) => {
        const ws = connect(userId);

        ws.onopen = () => {
          setIsStreaming(true);
          setStreamingContent('');
          ws.send(JSON.stringify({ message: text }));
        };

        let fullResponse = '';
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'chunk') {
              fullResponse += data.content;
              setStreamingContent(fullResponse);
            } else if (data.type === 'done') {
              setIsStreaming(false);
              setStreamingContent('');
              ws.close();
              resolve(data.full_response || fullResponse);
            } else if (data.type === 'error') {
              setIsStreaming(false);
              ws.close();
              resolve('');
            }
          } catch {}
        };

        ws.onerror = () => {
          setIsStreaming(false);
          resolve('');
        };

        ws.onclose = () => {
          setIsStreaming(false);
        };

        setTimeout(() => {
          if (ws.readyState === WebSocket.OPEN) ws.close();
          setIsStreaming(false);
          resolve(fullResponse);
        }, 30000);
      });
    },
    [connect]
  );

  return { sendStreaming, isStreaming };
}

const QUICK_PROMPTS = [
  'How am I doing today?',
  'What workout should I do?',
  'Give me sleep tips',
  'Check my ACWR',
];

export default function ChatScreen() {
  const userId = useUserStore((s) => s.userId);
  const { theme } = useTheme();
  const { llmOverride } = useDevSettings();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const tabBarHeight = useTabBarHeight();
  const styles = makeStyles(theme, tabBarHeight, insets.top);
  const { sendStreaming } = useStreamChat();

  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        "Hey! I'm your AdapFit AI coach. I can analyze your recovery data, suggest workouts, and help you stay on track. What's on your mind?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || loading) return;

      const userMsg: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: text.trim(),
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setInput('');
      setLoading(true);

      let reply = '';
      try {
        // A user-supplied key always goes through the REST path (the
        // socket endpoint doesn't accept an override) — streaming is
        // only used for the default server-side key.
        if (!llmOverride) {
          reply = await sendStreaming(text.trim(), userId);
        }

        if (!reply) {
          const history = messages.slice(-6).map((m) => ({ role: m.role, content: m.content }));
          const data = await api.chat(
            userId,
            text.trim(),
            history,
            llmOverride
              ? { provider: llmOverride.provider, api_key: llmOverride.apiKey, model: llmOverride.model, base_url: llmOverride.baseUrl }
              : undefined
          );
          reply = data.reply;
        }
      } catch {
        reply = "Couldn't reach the coach right now — check your connection and try again.";
      }

      if (reply) {
        const assistantMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: reply,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      }

      setLoading(false);
    },
    [messages, loading, llmOverride, sendStreaming]
  );

  const renderMessage = ({ item }: { item: Message }) => {
    const isUser = item.role === 'user';
    return (
      <View style={[styles.bubble, isUser ? styles.userBubble : styles.assistantBubble]}>
        <View style={styles.bubbleHeader}>
          {isUser ? <User size={14} color={theme.primaryLight} /> : <Bot size={14} color={theme.success} />}
          <Text style={styles.bubbleRole}>{isUser ? 'You' : 'Coach'}</Text>
        </View>
        <Text style={[styles.bubbleText, isUser ? styles.userText : styles.assistantText]}>
          {item.content}
        </Text>
      </View>
    );
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      {llmOverride && (
        <View style={styles.devBanner}>
          <Wrench size={12} color={theme.warning} />
          <Text style={styles.devBannerText}>Using your {llmOverride.provider} key</Text>
        </View>
      )}

      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={renderMessage}
        contentContainerStyle={styles.list}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
      />

      {messages.length <= 1 && (
        <View style={styles.quickPrompts}>
          {QUICK_PROMPTS.map((prompt) => (
            <TouchableOpacity
              key={prompt}
              style={styles.quickButton}
              onPress={() => { Haptics.selectionAsync(); sendMessage(prompt); }}
              accessibilityLabel={`Quick prompt: ${prompt}`}
              accessibilityRole="button"
            >
              <Text style={styles.quickText}>{prompt}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      <View style={styles.inputBar}>
        <TouchableOpacity
          style={styles.micButton}
          onPress={() => {
            Haptics.selectionAsync();
            setInput('How am I doing today?');
          }}
        >
          <Mic size={20} color={theme.primaryLight} />
        </TouchableOpacity>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Ask your coach..."
          placeholderTextColor={theme.textMuted}
          multiline
          maxLength={2000}
          editable={!loading}
          accessibilityLabel="Chat message input"
          accessibilityHint="Type a message to your AI fitness coach"
        />
        <TouchableOpacity
          style={[styles.sendButton, (!input.trim() || loading) && styles.sendDisabled]}
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); sendMessage(input); }}
          disabled={!input.trim() || loading}
        >
          <Send size={20} color={input.trim() && !loading ? '#fff' : theme.textMuted} />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

function makeStyles(theme: any, tabBarHeight: number, topInset: number) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.background },
    devBanner: {
      flexDirection: 'row', alignItems: 'center', gap: 6, justifyContent: 'center',
      paddingVertical: 6, paddingTop: topInset + 6, backgroundColor: theme.surface,
    },
    devBannerText: { fontSize: 11, color: theme.warning, fontWeight: '600' },
    list: { padding: 16, paddingBottom: 8, paddingTop: topInset + 12 },
    bubble: { maxWidth: '85%', borderRadius: 16, padding: 12, marginBottom: 12 },
    userBubble: { alignSelf: 'flex-end', backgroundColor: theme.primary, borderBottomRightRadius: 4 },
    assistantBubble: { alignSelf: 'flex-start', backgroundColor: theme.surface, borderBottomLeftRadius: 4 },
    bubbleHeader: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 4 },
    bubbleRole: { fontSize: 11, fontWeight: '600', color: theme.textSecondary },
    bubbleText: { fontSize: 15, lineHeight: 22 },
    userText: { color: '#fff' },
    assistantText: { color: theme.text },
    quickPrompts: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, paddingHorizontal: 16, marginBottom: 8 },
    quickButton: {
      backgroundColor: theme.surface, borderRadius: 20, paddingHorizontal: 14, paddingVertical: 8,
      borderWidth: 1, borderColor: theme.border,
    },
    quickText: { fontSize: 13, color: theme.primaryLight, fontWeight: '500' },
    inputBar: {
      flexDirection: 'row', alignItems: 'flex-end', padding: 12, gap: 8,
      // The tab bar is absolutely positioned, so the row has to reserve its
      // height or the bar covers the input and eats the taps.
      marginBottom: tabBarHeight,
      borderTopWidth: 1, borderTopColor: theme.border,
      backgroundColor: theme.background,
    },
    input: {
      flex: 1, backgroundColor: theme.surface, borderRadius: 20, paddingHorizontal: 16,
      paddingVertical: 10, fontSize: 15, color: theme.text, maxHeight: 100,
    },
    sendButton: { width: 40, height: 40, borderRadius: 20, backgroundColor: theme.primary, alignItems: 'center', justifyContent: 'center' },
    sendDisabled: { backgroundColor: theme.surface },
    micButton: {
      width: 40, height: 40, borderRadius: 20, backgroundColor: theme.surface,
      alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: theme.border,
    },
  });
}
