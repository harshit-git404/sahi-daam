import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import {
  getPhraseText,
  getVoiceAvailability,
  markVoiceLoadAttempted,
  speak,
  stop,
  subscribeToVoiceChanges,
  type VoiceAvailability,
} from '../services/voice';

export const AudioHaggleModal: React.FC = () => {
  const { isAudioModalOpen, setIsAudioModalOpen, selectedProduce, vendorAskingPrice, theme } = useApp();
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [activePhraseIndex, setActivePhraseIndex] = useState(0);
  const [voiceAvailability, setVoiceAvailability] = useState<VoiceAvailability>(() => getVoiceAvailability('hi'));
  const [voiceMessage, setVoiceMessage] = useState<string | null>(null);
  const playbackTokenRef = React.useRef(0);
  const isTerracotta = theme === 'terracotta';
  const phrases = selectedProduce.hagglePhrases ?? selectedProduce.bargainPhrases;
  const activePhrase = phrases[activePhraseIndex] ?? phrases[0];

  const updateVoiceAvailability = React.useCallback(() => {
    const nextAvailability = getVoiceAvailability('hi');
    setVoiceAvailability(nextAvailability);
    setVoiceMessage(nextAvailability.message);
  }, []);

  React.useEffect(() => {
    if (!isAudioModalOpen) {
      playbackTokenRef.current += 1;
      stop();
      setIsPlayingAudio(false);
      return;
    }

    updateVoiceAvailability();

    const unsubscribe = subscribeToVoiceChanges(updateVoiceAvailability);
    const voiceLoadTimer = window.setTimeout(() => {
      markVoiceLoadAttempted();
      updateVoiceAvailability();
    }, 1200);

    return () => {
      unsubscribe();
      window.clearTimeout(voiceLoadTimer);
    };
  }, [isAudioModalOpen, updateVoiceAvailability]);

  if (!isAudioModalOpen) return null;

  const playVoice = (phraseIndex: number) => {
    const phrase = phrases[phraseIndex];
    const phraseText = phrase ? getPhraseText(phrase, 'hi') : '';

    if (!phraseText) {
      playbackTokenRef.current += 1;
      stop();
      setIsPlayingAudio(false);
      setVoiceMessage('No Hindi phrase is available for this line.');
      return;
    }

    const playbackToken = playbackTokenRef.current + 1;
    playbackTokenRef.current = playbackToken;

    const result = speak(phraseText, 'hi', {
      onStart: () => {
        if (playbackTokenRef.current === playbackToken) {
          setIsPlayingAudio(true);
        }
      },
      onEnd: () => {
        if (playbackTokenRef.current === playbackToken) {
          setIsPlayingAudio(false);
        }
      },
      onError: () => {
        if (playbackTokenRef.current === playbackToken) {
          setIsPlayingAudio(false);
          setVoiceMessage('Speech playback stopped before finishing.');
        }
      },
    });

    if (result.ok) {
      setIsPlayingAudio(true);
      setVoiceMessage(null);
    } else {
      setIsPlayingAudio(false);
      setVoiceMessage(result.message);
      updateVoiceAvailability();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity animate-in fade-in"
        onClick={() => {
          playbackTokenRef.current += 1;
          stop();
          setIsAudioModalOpen(false);
        }}
      />

      {/* Modal Dialog */}
      <div className="relative w-full max-w-sm bg-white rounded-[28px] p-6 shadow-2xl z-10 border border-[#e4e2de] flex flex-col gap-4 animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div
              className={`w-9 h-9 rounded-full flex items-center justify-center text-white ${
                isTerracotta ? 'bg-[#9e3d00]' : 'bg-[#012d1d]'
              }`}
            >
              <span
                className="material-symbols-outlined text-[20px]"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                record_voice_over
              </span>
            </div>
            <div>
              <h3 className="font-display font-bold text-[16px] text-[#1b1c1a]">
                Haggle Voice Assistant
              </h3>
              <p className="text-[11px] text-[#594238]">
                Real-time spoken Mandi negotiation
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              playbackTokenRef.current += 1;
              stop();
              setIsAudioModalOpen(false);
            }}
            className="p-1 rounded-full text-[#594238] hover:bg-[#f5f3ef]"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        {/* Current Vendor Context */}
        <div className="bg-[#f5f3ef] rounded-2xl p-3.5 border border-[#e4e2de] text-center">
          <p className="text-[11px] font-semibold text-[#594238] uppercase tracking-wider">
            Current Negotiation Target
          </p>
          <p className="font-display text-[18px] font-bold text-[#1b1c1a] mt-0.5">
            {selectedProduce.name} · Asking ₹{vendorAskingPrice} → Offer ₹{selectedProduce.suggestedOfferPrice}
          </p>
        </div>

        {/* Audio Phrases List */}
        <div className="space-y-2.5 max-h-60 overflow-y-auto pr-1">
          {voiceMessage && (
            <p
              className={`rounded-xl border px-3 py-2 text-[11px] font-semibold ${
                voiceAvailability.status === 'loading'
                  ? 'border-[#e4e2de] bg-white text-[#594238]'
                  : 'border-[#fecaca] bg-[#fff7f5] text-[#7f1d1d]'
              }`}
              aria-live="polite"
            >
              {voiceMessage}
            </p>
          )}
          {phrases.map((phrase, idx) => (
            <div
              key={idx}
              onClick={() => {
                setActivePhraseIndex(idx);
                playVoice(idx);
              }}
              className={`p-3.5 rounded-2xl border cursor-pointer transition-all active:scale-[0.98] ${
                activePhraseIndex === idx
                  ? isTerracotta
                    ? 'border-[#9e3d00] bg-[#ffdbcd]/30 shadow-xs'
                    : 'border-[#012d1d] bg-[#c1ecd4]/30 shadow-xs'
                  : 'border-[#e4e2de] bg-white hover:bg-[#fbf9f5]'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <p className="font-semibold text-[14px] text-[#1b1c1a] leading-snug">
                  "{phrase.hindi}"
                </p>
                <button
                  className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${
                    activePhraseIndex === idx && isPlayingAudio
                      ? 'bg-[#006d37] text-white animate-pulse'
                      : 'bg-[#f5f3ef] text-[#594238]'
                  }`}
                >
                  <span
                    className="material-symbols-outlined text-[16px]"
                    style={{ fontVariationSettings: "'FILL' 1" }}
                  >
                    volume_up
                  </span>
                </button>
              </div>

              <p className="text-[12px] text-[#594238] italic mt-1">
                "{phrase.english}"
              </p>
            </div>
          ))}
        </div>

        {/* Pronunciation & Speak Action */}
        <button
          onClick={() => playVoice(activePhraseIndex)}
          disabled={voiceAvailability.status !== 'available' || !activePhrase}
          className={`w-full py-3.5 rounded-xl font-display font-semibold text-[15px] text-white flex items-center justify-center gap-2 shadow-md active:scale-95 transition-transform ${
            voiceAvailability.status !== 'available' || !activePhrase
              ? 'bg-[#9b9089] cursor-not-allowed'
              : isTerracotta
                ? 'bg-[#9e3d00]'
                : 'bg-[#012d1d]'
          }`}
        >
          <span className="material-symbols-outlined text-[20px]">
            {isPlayingAudio ? 'graphic_eq' : voiceAvailability.status === 'loading' ? 'hourglass_empty' : 'play_arrow'}
          </span>
          {isPlayingAudio ? 'Speaking in Hindi...' : 'Play Spoken Audio Tip'}
        </button>
      </div>
    </div>
  );
};
