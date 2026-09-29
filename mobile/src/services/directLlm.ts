/**
 * Calls the language model from the phone. Some providers refuse datacenter
 * addresses, so the server hands over the prompt and screens the reply instead.
 * The key ships in the app bundle: use a free, disposable one.
 */
const BASE = process.env.EXPO_PUBLIC_LLM_BASE_URL ?? '';
const KEY = process.env.EXPO_PUBLIC_LLM_KEY ?? '';
const MODELS = (process.env.EXPO_PUBLIC_LLM_MODELS ?? '').split(',').map((m: string) => m.trim()).filter(Boolean);

export const directLlmEnabled = !!(BASE && KEY && MODELS.length);

type Turn = { role: string; content: string };

/** First model that answers wins; null when every model fails or returns nothing. */
export async function askDirectLlm(system: string, history: Turn[], prompt: string): Promise<string | null> {
  const messages = [{ role: 'system', content: system }, ...history, { role: 'user', content: prompt }];
  for (const model of MODELS) {
    const abort = new AbortController();
    const timer = setTimeout(() => abort.abort(), 45000);
    try {
      const res = await fetch(`${BASE}/chat/completions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${KEY}` },
        body: JSON.stringify({ model, messages, temperature: 0.7, max_tokens: 900 }),
        signal: abort.signal,
      });
      if (res.ok) {
        const text = (await res.json())?.choices?.[0]?.message?.content;
        if (text) return text;
      }
    } catch {
      // try the next model
    } finally {
      clearTimeout(timer);
    }
  }
  return null;
}
