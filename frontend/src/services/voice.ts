import type { BargainPhrase, NegotiationLanguage } from '../types';

export type VoiceLanguage = NegotiationLanguage;

type PhraseField = 'hindi' | 'tamil' | 'english';

export interface VoiceLanguageConfig {
  code: VoiceLanguage;
  label: string;
  selectorLabel: string;
  locale: string;
  phraseField: PhraseField;
  rate: number;
  pitch: number;
  volume: number;
  loadingMessage: string;
  unavailableMessage: string;
}

export interface VoiceAvailability {
  status: 'unsupported' | 'loading' | 'available' | 'fallback' | 'unavailable';
  language: VoiceLanguage;
  voice: SpeechSynthesisVoice | null;
  message: string | null;
}

export interface SpeakEvents {
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (event: SpeechSynthesisErrorEvent) => void;
}

export type SpeakResult =
  | {
      ok: true;
      status: 'speaking';
      voice: SpeechSynthesisVoice | null;
      utterance: SpeechSynthesisUtterance;
      usedFallbackVoice: boolean;
    }
  | {
      ok: false;
      status: 'unsupported' | 'empty-text' | 'voice-unavailable' | 'speak-failed';
      message: string;
    };

export const VOICE_LANGUAGE_CONFIG: Record<VoiceLanguage, VoiceLanguageConfig> = {
  hi: {
    code: 'hi',
    label: 'Hindi',
    selectorLabel: 'हिन्दी',
    locale: 'hi-IN',
    phraseField: 'hindi',
    rate: 0.9,
    pitch: 1,
    volume: 1,
    loadingMessage: 'Checking installed Hindi voice...',
    unavailableMessage: 'Hindi-specific voice is unavailable. Using the browser default voice.',
  },
  ta: {
    code: 'ta',
    label: 'தமிழ் / Tamil',
    selectorLabel: 'தமிழ்',
    locale: 'ta-IN',
    phraseField: 'tamil',
    rate: 0.9,
    pitch: 1,
    volume: 1,
    loadingMessage: 'Checking installed Tamil voice...',
    unavailableMessage: 'Tamil-specific voice is unavailable. Using the browser default voice.',
  },
  en: {
    code: 'en',
    label: 'English',
    selectorLabel: 'English',
    locale: 'en-IN',
    phraseField: 'english',
    rate: 0.95,
    pitch: 1,
    volume: 1,
    loadingMessage: 'Checking installed English voice...',
    unavailableMessage: 'English-specific voice is unavailable. Using the browser default voice.',
  },
};

export const VOICE_LANGUAGE_ORDER: VoiceLanguage[] = ['hi', 'ta', 'en'];

export const SUPPORTED_VOICE_LANGUAGES: VoiceLanguageConfig[] = VOICE_LANGUAGE_ORDER.map(
  (language) => VOICE_LANGUAGE_CONFIG[language]
);

let cachedVoices: SpeechSynthesisVoice[] = [];
let voiceLoadAttempted = false;

function getSynth(): SpeechSynthesis | null {
  if (
    typeof window === 'undefined' ||
    !('speechSynthesis' in window) ||
    typeof SpeechSynthesisUtterance === 'undefined'
  ) {
    return null;
  }

  return window.speechSynthesis;
}

function normalizeLocale(locale: string): string {
  return locale.trim().toLowerCase();
}

function refreshVoices(markAttempted = false): SpeechSynthesisVoice[] {
  const synth = getSynth();

  if (!synth) {
    cachedVoices = [];
    voiceLoadAttempted = true;
    return cachedVoices;
  }

  cachedVoices = synth.getVoices();

  if (cachedVoices.length > 0 || markAttempted) {
    voiceLoadAttempted = true;
  }

  return cachedVoices;
}

function findExactVoice(voices: SpeechSynthesisVoice[], locale: string): SpeechSynthesisVoice | null {
  const normalizedLocale = normalizeLocale(locale);
  return voices.find((voice) => normalizeLocale(voice.lang) === normalizedLocale) ?? null;
}

function findFamilyVoice(voices: SpeechSynthesisVoice[], family: string): SpeechSynthesisVoice | null {
  const normalizedFamily = normalizeLocale(family);
  return voices.find((voice) => normalizeLocale(voice.lang).startsWith(normalizedFamily)) ?? null;
}

export function isSupported(): boolean {
  return getSynth() !== null;
}

export function getAvailableVoices(): SpeechSynthesisVoice[] {
  return refreshVoices();
}

export function markVoiceLoadAttempted(): void {
  refreshVoices(true);
}

export function getBestVoice(language: VoiceLanguage): SpeechSynthesisVoice | null {
  const voices = refreshVoices();
  const config = VOICE_LANGUAGE_CONFIG[language];

  if (language === 'hi') {
    return findExactVoice(voices, config.locale) ?? findFamilyVoice(voices, 'hi-');
  }

  if (language === 'ta') {
    return findExactVoice(voices, config.locale) ?? findFamilyVoice(voices, 'ta-');
  }

  return (
    findExactVoice(voices, config.locale) ??
    findExactVoice(voices, 'en-GB') ??
    findExactVoice(voices, 'en-US') ??
    findFamilyVoice(voices, 'en-')
  );
}

export function getVoiceAvailability(language: VoiceLanguage): VoiceAvailability {
  const config = VOICE_LANGUAGE_CONFIG[language];

  if (!isSupported()) {
    return {
      status: 'unsupported',
      language,
      voice: null,
      message: 'Speech playback is not supported in this browser.',
    };
  }

  const voice = getBestVoice(language);

  if (voice) {
    return {
      status: 'available',
      language,
      voice,
      message: null,
    };
  }

  if (cachedVoices.length === 0 && !voiceLoadAttempted) {
    return {
      status: 'loading',
      language,
      voice: null,
      message: config.loadingMessage,
    };
  }

  return {
    status: 'fallback',
    language,
    voice: null,
    message: config.unavailableMessage,
  };
}

export function subscribeToVoiceChanges(listener: () => void): () => void {
  const synth = getSynth();

  if (!synth) {
    return () => undefined;
  }

  const handleVoicesChanged = () => {
    refreshVoices(true);
    listener();
  };

  synth.addEventListener('voiceschanged', handleVoicesChanged);
  return () => synth.removeEventListener('voiceschanged', handleVoicesChanged);
}

export function getPhraseText(phrase: BargainPhrase, language: VoiceLanguage): string {
  const field = VOICE_LANGUAGE_CONFIG[language].phraseField;
  const value = phrase[field];
  return typeof value === 'string' ? value.trim() : '';
}

export function stop(): void {
  const synth = getSynth();
  if (synth) {
    synth.cancel();
  }
}

export function speak(text: string, language: VoiceLanguage, events: SpeakEvents = {}): SpeakResult {
  const cleanText = text.trim();
  const config = VOICE_LANGUAGE_CONFIG[language];

  if (!cleanText) {
    return {
      ok: false,
      status: 'empty-text',
      message: `No ${config.label} phrase is available for speech.`,
    };
  }

  const synth = getSynth();

  if (!synth) {
    return {
      ok: false,
      status: 'unsupported',
      message: 'Speech playback is not supported in this browser.',
    };
  }

  const voice = getBestVoice(language);

  try {
    synth.cancel();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = config.locale;
    utterance.voice = voice;
    utterance.rate = config.rate;
    utterance.pitch = config.pitch;
    utterance.volume = config.volume;
    utterance.onstart = () => events.onStart?.();
    utterance.onend = () => events.onEnd?.();
    utterance.onerror = (event) => events.onError?.(event);

    synth.speak(utterance);

    return {
      ok: true,
      status: 'speaking',
      voice,
      utterance,
      usedFallbackVoice: voice === null,
    };
  } catch {
    return {
      ok: false,
      status: 'speak-failed',
      message: 'Speech playback could not start on this device.',
    };
  }
}
