import React, { useState } from 'react';
import { useApp } from '../context/AppContext';

export const AudioHaggleModal: React.FC = () => {
  const { isAudioModalOpen, setIsAudioModalOpen, selectedProduce, vendorAskingPrice, theme } = useApp();
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [activePhraseIndex, setActivePhraseIndex] = useState(0);
  const isTerracotta = theme === 'terracotta';

  if (!isAudioModalOpen) return null;

  const phrases = selectedProduce.bargainPhrases;

  const playVoice = (text: string) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.95;
      utterance.pitch = 1.0;
      utterance.onstart = () => setIsPlayingAudio(true);
      utterance.onend = () => setIsPlayingAudio(false);
      utterance.onerror = () => setIsPlayingAudio(false);
      window.speechSynthesis.speak(utterance);
    } else {
      setIsPlayingAudio(true);
      setTimeout(() => setIsPlayingAudio(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity animate-in fade-in"
        onClick={() => {
          if ('speechSynthesis' in window) window.speechSynthesis.cancel();
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
              if ('speechSynthesis' in window) window.speechSynthesis.cancel();
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
          {phrases.map((phrase, idx) => (
            <div
              key={idx}
              onClick={() => {
                setActivePhraseIndex(idx);
                playVoice(phrase.hindi);
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
          onClick={() => playVoice(phrases[activePhraseIndex].hindi)}
          className={`w-full py-3.5 rounded-xl font-display font-semibold text-[15px] text-white flex items-center justify-center gap-2 shadow-md active:scale-95 transition-transform ${
            isTerracotta ? 'bg-[#9e3d00]' : 'bg-[#012d1d]'
          }`}
        >
          <span className="material-symbols-outlined text-[20px]">
            {isPlayingAudio ? 'graphic_eq' : 'play_arrow'}
          </span>
          {isPlayingAudio ? 'Speaking in Hindi...' : 'Play Spoken Audio Tip'}
        </button>
      </div>
    </div>
  );
};
