import React from 'react';
import { useApp } from '../context/AppContext';
import { Header } from './Header';
import {
  getPhraseText,
  getVoiceAvailability,
  markVoiceLoadAttempted,
  speak,
  stop,
  subscribeToVoiceChanges,
  SUPPORTED_VOICE_LANGUAGES,
  VOICE_LANGUAGE_CONFIG,
  type VoiceAvailability,
  type VoiceLanguage,
} from '../services/voice';
import { formatRupees, formatRupeesPerUnit } from '../services/format';

// Decision config
type Decision = 'GOOD_DEAL' | 'FAIR_PRICE' | 'SLIGHTLY_HIGH' | 'OVERPRICED' | 'UNUSUALLY_CHEAP';

const DECISION_CONFIG: Record<Decision, {
  icon: string;
  label: string;
  bgClass: string;
  borderClass: string;
  textClass: string;
  badgeBg: string;
  badgeText: string;
}> = {
  GOOD_DEAL: { icon: 'thumb_up', label: 'Good Deal', bgClass: 'bg-[#f0fdf4]', borderClass: 'border-[#bbf7d0]', textClass: 'text-[#166534]', badgeBg: 'bg-[#dcfce7]', badgeText: 'text-[#166534]' },
  FAIR_PRICE: { icon: 'check_circle', label: 'Fair Price', bgClass: 'bg-[#f2fcf5]', borderClass: 'border-[#c6efd6]', textClass: 'text-[#006d37]', badgeBg: 'bg-[#d1fae5]', badgeText: 'text-[#065f46]' },
  SLIGHTLY_HIGH: { icon: 'arrow_upward', label: 'Slightly High', bgClass: 'bg-[#fffbeb]', borderClass: 'border-[#fde68a]', textClass: 'text-[#92400e]', badgeBg: 'bg-[#fef9c3]', badgeText: 'text-[#713f12]' },
  OVERPRICED: { icon: 'trending_up', label: 'Overpriced', bgClass: 'bg-[#fff0ee]', borderClass: 'border-[#ffdad6]', textClass: 'text-[#93000a]', badgeBg: 'bg-[#ffe4e1]', badgeText: 'text-[#7f1d1d]' },
  UNUSUALLY_CHEAP: { icon: 'warning', label: 'Unusually Cheap', bgClass: 'bg-[#fffae0]', borderClass: 'border-[#fde68a]', textClass: 'text-[#806b00]', badgeBg: 'bg-[#fef9c3]', badgeText: 'text-[#713f12]' },
};

// PriceCell
interface PriceCellProps { label: string; value?: number; accent?: boolean; terracotta?: boolean; }
const PriceCell: React.FC<PriceCellProps> = ({ label, value, accent, terracotta }) => {
  if (value === undefined) return null;
  return (
    <div className="flex flex-col items-center gap-0.5 min-w-0">
      <span className="text-[9px] font-bold uppercase tracking-widest text-[#594238] text-center">{label}</span>
      <span className={`font-display text-[24px] font-extrabold leading-none ${accent ? (terracotta ? 'text-[#9e3d00]' : 'text-[#012d1d]') : 'text-[#1b1c1a]'}`}>
        {formatRupees(value)}
      </span>
    </div>
  );
};

// Main component
export const BargainScreen: React.FC = () => {
  const {
    setCurrentScreen,
    selectedProduce,
    vendorAskingPrice,
    setVendorAskingPrice,
    negotiationState,
    setNegotiationLanguage,
    recordPurchase,
    setIsAudioModalOpen,
    theme,
  } = useApp();
  const isTerracotta = theme === 'terracotta';
  const selectedLanguage = negotiationState.language;
  const [voiceAvailability, setVoiceAvailability] = React.useState<VoiceAvailability>(() => getVoiceAvailability(selectedLanguage));
  const [playingPhraseIndex, setPlayingPhraseIndex] = React.useState<number | null>(null);
  const [voiceMessage, setVoiceMessage] = React.useState<string | null>(null);
  const playbackTokenRef = React.useRef(0);
  const selectedLanguageConfig = VOICE_LANGUAGE_CONFIG[selectedLanguage];

  const fairAvg = Math.round((selectedProduce.retailFairMin + selectedProduce.retailFairMax) / 2);
  const fallbackBuyPrice = Math.max(selectedProduce.wholesalePrice + 5, Math.round(fairAvg + (vendorAskingPrice > fairAvg ? fairAvg * 0.05 : 0)));

  const decision = selectedProduce.decision as Decision | undefined;
  const cfg = decision ? DECISION_CONFIG[decision] : undefined;
  const showNegotiation = decision === 'OVERPRICED' || decision === 'SLIGHTLY_HIGH';

  const confirmedBuyPrice = negotiationState.recommendedNextOffer ?? selectedProduce.targetPrice ?? selectedProduce.startingOffer ?? selectedProduce.suggestedOfferPrice ?? fallbackBuyPrice;
  const currentOffer = negotiationState.userCurrentOffer ?? selectedProduce.startingOffer ?? selectedProduce.suggestedOfferPrice;
  const latestVendorCounter = negotiationState.latestVendorCounterOffer ?? vendorAskingPrice;
  const isNegotiationUpdating = negotiationState.status === 'listening' || negotiationState.status === 'processing';
  const statusLabel =
    negotiationState.status === 'listening'
      ? 'Listening...'
      : negotiationState.status === 'processing'
        ? 'Processing vendor response...'
        : negotiationState.status === 'timeout'
          ? 'Still waiting for advice'
          : negotiationState.status === 'error'
            ? 'Using last recommendation'
            : 'Live negotiation';

  const handleDecrease = () => { setVendorAskingPrice(prev => Math.max(selectedProduce.wholesalePrice || 5, prev - 5)); if (navigator.vibrate) navigator.vibrate(20); };
  const handleIncrease = () => { setVendorAskingPrice(prev => Math.min(200, prev + 5)); if (navigator.vibrate) navigator.vibrate(20); };
  const handleBuy = () => { recordPurchase(confirmedBuyPrice); setCurrentScreen('history'); };

  const minSlider = 10;
  const maxSlider = Math.max(100, vendorAskingPrice + 10);
  const phrases = selectedProduce.hagglePhrases ?? selectedProduce.bargainPhrases ?? [];

  const updateVoiceAvailability = React.useCallback(() => {
    const nextAvailability = getVoiceAvailability(selectedLanguage);
    setVoiceAvailability(nextAvailability);
    setVoiceMessage(nextAvailability.message);
  }, [selectedLanguage]);

  React.useEffect(() => {
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
  }, [updateVoiceAvailability]);

  React.useEffect(() => {
    playbackTokenRef.current += 1;
    stop();
    setPlayingPhraseIndex(null);
  }, [selectedLanguage]);

  React.useEffect(() => () => {
    playbackTokenRef.current += 1;
    stop();
  }, []);

  const handleLanguageChange = (language: VoiceLanguage) => {
    setNegotiationLanguage(language);
  };

  const handleSpeakPhrase = (phrase: (typeof phrases)[number], phraseIndex: number) => {
    const phraseText = getPhraseText(phrase, selectedLanguage);

    if (!phraseText) {
      playbackTokenRef.current += 1;
      stop();
      setPlayingPhraseIndex(null);
      setVoiceMessage(`No ${selectedLanguageConfig.label} phrase is available for this line.`);
      return;
    }

    if (playingPhraseIndex === phraseIndex) {
      playbackTokenRef.current += 1;
      stop();
      setPlayingPhraseIndex(null);
      setVoiceMessage(null);
      return;
    }

    const playbackToken = playbackTokenRef.current + 1;
    playbackTokenRef.current = playbackToken;

    const result = speak(phraseText, selectedLanguage, {
      onStart: () => {
        if (playbackTokenRef.current === playbackToken) {
          setPlayingPhraseIndex(phraseIndex);
        }
      },
      onEnd: () => {
        if (playbackTokenRef.current === playbackToken) {
          setPlayingPhraseIndex(null);
        }
      },
      onError: () => {
        if (playbackTokenRef.current === playbackToken) {
          setPlayingPhraseIndex(null);
          setVoiceMessage('Speech playback stopped before finishing.');
        }
      },
    });

    if (result.ok) {
      setPlayingPhraseIndex(phraseIndex);
      setVoiceMessage(null);
    } else {
      setPlayingPhraseIndex(null);
      setVoiceMessage(result.message);
      updateVoiceAvailability();
    }
  };

  return (
    <div className="min-h-screen bg-[#fbf9f5] flex flex-col pb-12 antialiased relative overflow-x-hidden">
      <Header title={`${selectedProduce.name} Bargain`} showBack onBack={() => setCurrentScreen('price_breakdown')} />

      {/* Decorative glow */}
      <div className={`absolute top-10 right-[-15%] w-72 h-72 rounded-full blur-[90px] opacity-25 pointer-events-none ${isTerracotta ? 'bg-[#ffb595]' : 'bg-[#a5d0b9]'}`} />

      <main className="flex-1 max-w-md mx-auto w-full px-4 py-4 flex flex-col gap-4 relative z-10">

        {/* Price stepper */}
        <section id="vendor-price-stepper-card" className="bg-white rounded-[24px] p-5 shadow-sm border border-[#e4e2de]/70 flex flex-col gap-4">
          <label className="font-semibold text-[14px] text-[#1b1c1a] text-center block">What is the vendor asking?</label>
          <div className="flex items-center justify-between gap-3">
            <button id="decrease-price-btn" aria-label="Decrease price" onClick={handleDecrease}
              className="w-12 h-12 rounded-full bg-[#f5f3ef] flex items-center justify-center text-[#1b1c1a] hover:bg-[#eae8e4] active:scale-90 transition-all border border-[#e0c0b2]/40">
              <span className="material-symbols-outlined text-[22px]">remove</span>
            </button>
            <div className="flex-1 text-center">
              <div className="flex items-center justify-center">
                <span className="text-[22px] font-bold text-[#594238] mr-0.5">{formatRupees(0).charAt(0)}</span>
                <input id="vendor-price-input" aria-label="Vendor asking price" type="number" value={vendorAskingPrice}
                  onChange={e => setVendorAskingPrice(Math.max(1, Number(e.target.value)))}
                  className="w-24 bg-transparent border-none text-center font-display text-[34px] font-extrabold text-[#1b1c1a] focus:ring-0 focus:outline-none p-0" />
              </div>
              <div className="w-full h-[2px] bg-[#e4e2de] rounded-full mt-1">
                <div className={`h-full mx-auto w-2/3 rounded-full ${isTerracotta ? 'bg-[#9e3d00]' : 'bg-[#012d1d]'}`} />
              </div>
            </div>
            <button id="increase-price-btn" aria-label="Increase price" onClick={handleIncrease}
              className="w-12 h-12 rounded-full bg-[#f5f3ef] flex items-center justify-center text-[#1b1c1a] hover:bg-[#eae8e4] active:scale-90 transition-all border border-[#e0c0b2]/40">
              <span className="material-symbols-outlined text-[22px]">add</span>
            </button>
          </div>
          <div className="px-1">
            <input id="vendor-price-slider" aria-label="Price range slider" type="range" min={minSlider} max={maxSlider}
              value={vendorAskingPrice} onChange={e => setVendorAskingPrice(Number(e.target.value))}
              className="w-full h-2 bg-[#e4e2de] rounded-lg appearance-none cursor-pointer accent-[#9e3d00]" />
            <div className="flex justify-between mt-1 text-[11px] font-medium text-[#594238]">
              <span>{formatRupees(minSlider)}</span>
              <span>Fair avg {formatRupees(fairAvg)}</span>
              <span>{formatRupees(maxSlider)}</span>
            </div>
          </div>
          <div
            className={`rounded-xl border px-3 py-2 text-[12px] font-semibold flex items-center justify-between gap-2 ${
              negotiationState.status === 'error' || negotiationState.status === 'timeout'
                ? 'bg-[#fff7f5] border-[#fecaca] text-[#7f1d1d]'
                : isNegotiationUpdating
                  ? 'bg-[#fffbeb] border-[#fde68a] text-[#713f12]'
                  : 'bg-[#f0fdf4] border-[#bbf7d0] text-[#166534]'
            }`}
            aria-live="polite"
          >
            <span className="flex items-center gap-1.5">
              <span className={`material-symbols-outlined text-[16px] ${isNegotiationUpdating ? 'animate-spin' : ''}`}>
                {negotiationState.status === 'listening' ? 'hearing' : negotiationState.status === 'processing' ? 'sync' : negotiationState.status === 'ready' ? 'check_circle' : 'info'}
              </span>
              {statusLabel}
            </span>
            <span className="text-[11px] opacity-80">{selectedLanguageConfig.label}</span>
          </div>
          {negotiationState.error && (
            <p className="text-[11px] font-medium text-[#7f1d1d]" aria-live="polite">
              {negotiationState.error}
            </p>
          )}
        </section>

        {/* ── DECISION ── */}
        {decision && cfg && (
          <>
            <section id="decision-card" className={`rounded-[24px] p-5 border shadow-xs ${cfg.bgClass} ${cfg.borderClass}`}>
              <h3 className="text-[11px] font-bold text-[#594238] mb-3 uppercase tracking-widest opacity-80">
                What's The Verdict?
              </h3>
              <div className="flex items-center gap-2 mb-2 flex-wrap">
                <span className={`material-symbols-outlined text-[24px] ${cfg.textClass}`} style={{ fontVariationSettings: "'FILL' 1" }}>
                  {cfg.icon}
                </span>
                <h2 className={`font-display text-[22px] font-extrabold tracking-tight ${cfg.textClass}`}>
                  {cfg.label}
                </h2>
                {selectedProduce.severity && selectedProduce.severity !== 'NONE' && (
                  <span className={`ml-auto text-[9px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full ${cfg.badgeBg} ${cfg.badgeText}`}>
                    {selectedProduce.severity}
                  </span>
                )}
              </div>
              <p className="text-[15px] font-medium text-[#1b1c1a] leading-snug">
                {selectedProduce.recommendation?.headline}
              </p>
            </section>

            {/* ── NEGOTIATION STRATEGY (WHAT SHOULD I DO?) ── */}
            {showNegotiation && (
              <section id="negotiation-strategy-card" className="bg-white rounded-[24px] p-5 border border-[#e4e2de] shadow-sm">
                <p className="text-[11px] font-bold text-[#594238] mb-4 uppercase tracking-widest">What Should I Do?</p>
                <div className="grid grid-cols-2 gap-2 px-1">
                  <div key={`vendor-${vendorAskingPrice}`} className="rounded-xl bg-[#f5f3ef] border border-[#e4e2de]/70 p-3 animate-in fade-in zoom-in-95 duration-200">
                    <PriceCell label="Vendor Asking" value={vendorAskingPrice} />
                  </div>
                  <div key={`offer-${currentOffer}`} className="rounded-xl bg-[#f5f3ef] border border-[#e4e2de]/70 p-3 animate-in fade-in zoom-in-95 duration-200">
                    <PriceCell label="Your Offer" value={currentOffer} accent terracotta={isTerracotta} />
                  </div>
                  <div key={`counter-${latestVendorCounter}`} className="rounded-xl bg-[#f5f3ef] border border-[#e4e2de]/70 p-3 animate-in fade-in zoom-in-95 duration-200">
                    <PriceCell label="Vendor Counter" value={latestVendorCounter} />
                  </div>
                  <div key={`next-${confirmedBuyPrice}`} className="rounded-xl bg-[#fff7f2] border border-[#e0c0b2]/70 p-3 animate-in fade-in zoom-in-95 duration-200">
                    <PriceCell label="Next Offer" value={confirmedBuyPrice} accent terracotta={isTerracotta} />
                  </div>
                </div>
                {selectedProduce.potentialSaving ? (
                  <div className="mt-5 bg-[#f0fdf4] border border-[#bbf7d0] text-[#166534] px-4 py-2.5 rounded-xl text-center font-bold text-[13px]">
                    Potential saving: {formatRupeesPerUnit(selectedProduce.potentialSaving, selectedProduce.unit)}
                  </div>
                ) : null}
              </section>
            )}

            {/* ── BELOW FAIR (GOOD_DEAL) ── */}
            {decision === 'GOOD_DEAL' && selectedProduce.belowFairAmount ? (
              <section className="bg-[#f0fdf4] border border-[#bbf7d0] rounded-[24px] p-4 text-center shadow-xs">
                <p className="text-[13px] font-bold text-[#166534]">
                  {formatRupees(selectedProduce.belowFairAmount)} below estimated fair minimum - already a good deal.
                </p>
              </section>
            ) : null}

            {/* ── QUALITY CAUTION ── */}
            {selectedProduce.qualityContext?.caution && (
              <section className="bg-[#fffbeb] border border-[#fde68a] rounded-[24px] p-4 flex items-start gap-2 shadow-xs">
                <span className="material-symbols-outlined text-[18px] text-[#92400e] mt-0.5 flex-shrink-0" style={{ fontVariationSettings: "'FILL' 1" }}>info</span>
                <p className="text-[13px] font-semibold text-[#92400e] leading-snug">{selectedProduce.qualityContext.caution}</p>
              </section>
            )}
            
            {/* ── WHY ── */}
            <section id="why-card" className="bg-white border border-[#e4e2de] rounded-[24px] p-5 shadow-xs">
              <p className="text-[11px] font-bold text-[#594238] mb-3 uppercase tracking-widest">Why?</p>
              
              <div className="flex flex-col gap-2.5 mb-4 bg-[#f5f3ef] rounded-xl p-3 border border-[#e4e2de]/60">
                <div className="flex items-center justify-between text-[13px] text-[#594238]">
                  <span>Vendor asking:</span>
                  <span className="font-bold text-[#1b1c1a]">{formatRupeesPerUnit(vendorAskingPrice, selectedProduce.unit)}</span>
                </div>
                <div className="flex items-center justify-between text-[13px] text-[#594238]">
                  <span>Fair range:</span>
                  <span className="font-bold text-[#1b1c1a]">{formatRupees(selectedProduce.retailFairMin)}-{formatRupeesPerUnit(selectedProduce.retailFairMax, selectedProduce.unit)}</span>
                </div>
              </div>

              {selectedProduce.alternatives?.quickcommerce && (
                <div className="mb-4 text-[13.5px] text-[#1b1c1a] leading-relaxed px-1">
                  <span className="font-semibold">{selectedProduce.alternatives.quickcommerce.source} is {formatRupeesPerUnit(selectedProduce.alternatives.quickcommerce.price, selectedProduce.unit)}</span>, but your local fair range is {formatRupees(selectedProduce.retailFairMin)}-{formatRupeesPerUnit(selectedProduce.retailFairMax, selectedProduce.unit)}.
                </div>
              )}
              
              <div className="text-[13.5px] text-[#1b1c1a] leading-relaxed px-1">
                {selectedProduce.recommendation?.explanation ?? selectedProduce.haggleReasoning}
              </div>
            </section>
          </>
        )}

        {/* ── PHRASEBOOK ── */}
        {phrases.length > 0 && (
          <section id="phrasebook-card" className="bg-[#f5f3ef] rounded-[20px] p-4 border border-[#e4e2de]">
            <div className="flex items-start justify-between gap-3 mb-3">
              <span className="text-[11px] font-bold uppercase tracking-widest text-[#594238] flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[15px] text-[#9e3d00]">record_voice_over</span>
                What To Say
              </span>
              <div
                className="flex rounded-full bg-white border border-[#e4e2de] p-0.5 shrink-0"
                role="radiogroup"
                aria-label="Phrase language"
              >
                {SUPPORTED_VOICE_LANGUAGES.map((language) => {
                  const isSelected = selectedLanguage === language.code;

                  return (
                    <button
                      key={language.code}
                      type="button"
                      role="radio"
                      aria-checked={isSelected}
                      onClick={() => handleLanguageChange(language.code)}
                      className={`min-w-[58px] rounded-full px-2.5 py-1 text-[11px] font-bold transition-all ${
                        isSelected
                          ? isTerracotta
                            ? 'bg-[#9e3d00] text-white shadow-xs'
                            : 'bg-[#012d1d] text-white shadow-xs'
                          : 'text-[#594238] hover:bg-[#f5f3ef]'
                      }`}
                    >
                      {language.selectorLabel}
                    </button>
                  );
                })}
              </div>
            </div>
            {voiceMessage && (
              <p
                className={`mb-3 rounded-xl border px-3 py-2 text-[11px] font-semibold ${
                  voiceAvailability.status === 'loading' || voiceAvailability.status === 'fallback'
                    ? 'border-[#e4e2de] bg-white text-[#594238]'
                    : 'border-[#fecaca] bg-[#fff7f5] text-[#7f1d1d]'
                }`}
                aria-live="polite"
              >
                {voiceMessage}
              </p>
            )}
            <div className="space-y-2">
              {phrases.slice(0, 2).map((phrase, idx) => {
                const primaryText = getPhraseText(phrase, selectedLanguage);
                const isPlaying = playingPhraseIndex === idx;
                const canSpeak = (voiceAvailability.status === 'available' || voiceAvailability.status === 'fallback') && primaryText.length > 0;
                const disabledReason = primaryText
                  ? voiceAvailability.message ?? `${selectedLanguageConfig.label} voice is not ready.`
                  : `No ${selectedLanguageConfig.label} phrase is available for this line.`;

                return (
                  <div key={idx} className="p-3 rounded-xl bg-white border border-[#e4e2de]/70 relative pr-12">
                    <p className={`font-semibold text-[#1b1c1a] leading-snug ${selectedLanguage === 'en' ? 'text-[14px]' : 'text-[15px]'}`}>
                      {primaryText ? `"${primaryText}"` : `${selectedLanguageConfig.label} phrase unavailable`}
                    </p>
                    {selectedLanguage !== 'en' && phrase.english && (
                      <p className="text-[11px] text-[#594238] italic mt-1">"{phrase.english}"</p>
                    )}
                    {selectedLanguage === 'hi' && phrase.phonetic && (
                      <p className="text-[11px] text-[#594238] font-medium mt-0.5">{phrase.phonetic}</p>
                    )}
                    <button
                      type="button"
                      onClick={() => handleSpeakPhrase(phrase, idx)}
                      disabled={!canSpeak}
                      className={`absolute right-2.5 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center rounded-full transition-all ${
                        isPlaying
                          ? isTerracotta
                            ? 'bg-[#9e3d00] text-white animate-pulse'
                            : 'bg-[#012d1d] text-white animate-pulse'
                          : canSpeak
                            ? 'bg-[#f5f3ef] text-[#1b1c1a] hover:bg-[#eae8e4] active:scale-95'
                            : 'bg-[#efeeea] text-[#9b9089] cursor-not-allowed'
                      }`}
                      aria-label={isPlaying ? `Stop ${selectedLanguageConfig.label} phrase` : `Listen in ${selectedLanguageConfig.label}`}
                      title={canSpeak ? `Listen in ${selectedLanguageConfig.label}` : disabledReason}
                    >
                      <span className="material-symbols-outlined text-[17px]">
                        {isPlaying ? 'stop_circle' : voiceAvailability.status === 'loading' ? 'hourglass_empty' : 'volume_up'}
                      </span>
                    </button>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* Actions */}
        <div className="flex flex-col gap-3 mt-1">
          <button id="start-haggle-assistant-btn" onClick={() => setIsAudioModalOpen(true)}
            className="relative w-full bg-[#efeeea] border border-[#e4e2de] rounded-2xl py-3.5 px-4 flex items-center justify-center gap-3 hover:bg-[#eae8e4] active:scale-[0.98] transition-all group">
            <div className="absolute top-2 right-3 bg-[#ffddb9] text-[#663e00] px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider">SOON</div>
            <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white shadow-md group-hover:scale-105 transition-transform ${isTerracotta ? 'bg-[#c64f00]' : 'bg-[#1b4332]'}`}>
              <span className="material-symbols-outlined text-[20px]" style={{ fontVariationSettings: "'FILL' 1" }}>mic</span>
            </div>
            <span className="font-display font-semibold text-[15px] text-[#1b1c1a]">Start Haggle Assistant</span>
          </button>

          <button id="i-bought-it-btn" onClick={handleBuy}
            className={`w-full text-white font-display text-[17px] font-bold rounded-2xl py-4 shadow-[0px_8px_24px_rgba(211,84,0,0.22)] active:scale-[0.98] transition-all flex items-center justify-center gap-2 ${isTerracotta ? 'bg-[#9e3d00]' : 'bg-[#012d1d]'}`}>
            <span className="material-symbols-outlined text-[21px]" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
            I Bought It at {formatRupees(confirmedBuyPrice)}
          </button>
          <p className="text-center text-[12px] text-[#594238]">Saves to your purchase history</p>
        </div>
      </main>
    </div>
  );
};
