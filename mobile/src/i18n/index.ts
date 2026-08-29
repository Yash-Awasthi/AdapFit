/**
 * AdapFit Internationalization (i18n)
 * Supports: English, Spanish, French, German, Chinese, Japanese, Korean, Arabic, Hindi, Portuguese
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import en from './en.json';
import es from './es.json';
import fr from './fr.json';

const TRANSLATIONS: Record<string, any> = { en, es, fr };

export type Language = 'en' | 'es' | 'fr' | 'de' | 'zh' | 'ja' | 'ko' | 'ar' | 'hi' | 'pt';

export const LANGUAGES: { code: Language; name: string; nativeName: string; flag: string }[] = [
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Spanish', nativeName: 'Espanol', flag: '🇪🇸' },
  { code: 'fr', name: 'French', nativeName: 'Francais', flag: '🇫🇷' },
  { code: 'de', name: 'German', nativeName: 'Deutsch', flag: '🇩🇪' },
  { code: 'zh', name: 'Chinese', nativeName: '中文', flag: '🇨🇳' },
  { code: 'ja', name: 'Japanese', nativeName: '日本語', flag: '🇯🇵' },
  { code: 'ko', name: 'Korean', nativeName: '한국어', flag: '🇰🇷' },
  { code: 'ar', name: 'Arabic', nativeName: 'العربية', flag: '🇸🇦' },
  { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी', flag: '🇮🇳' },
  { code: 'pt', name: 'Portuguese', nativeName: 'Portugues', flag: '🇧🇷' },
];

let currentLanguage: Language = 'en';

export async function setLanguage(lang: Language) {
  currentLanguage = lang;
  await AsyncStorage.setItem('adapfit_lang', lang);
}

export async function getLanguage(): Promise<Language> {
  const saved = await AsyncStorage.getItem('adapfit_lang');
  if (saved && saved in TRANSLATIONS) {
    currentLanguage = saved as Language;
  }
  return currentLanguage;
}

export function t(key: string, params?: Record<string, string | number>): string {
  const langData = TRANSLATIONS[currentLanguage] || TRANSLATIONS.en;
  const keys = key.split('.');
  let value: any = langData;
  for (const k of keys) {
    value = value?.[k];
  }
  if (typeof value !== 'string') {
    // Fallback to English
    let fallback: any = TRANSLATIONS.en;
    for (const k of keys) {
      fallback = fallback?.[k];
    }
    value = typeof fallback === 'string' ? fallback : key;
  }
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      value = value.replace(`{{${k}}}`, String(v));
    });
  }
  return value;
}

export default { t, setLanguage, getLanguage, LANGUAGES };
