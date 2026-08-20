import React, { createContext, useContext, useState, useEffect } from 'react';
import { Screen, ProduceItem, PurchaseRecord, MandiLocation, AppTheme, NegotiationLanguage, NegotiationState } from '../types';
import { PRODUCE_DATABASE } from '../data/produceData';
import { MANDI_LOCATIONS } from '../data/mandiLocations';
import confetti from 'canvas-confetti';
import { fetchScanResult, fetchHaggleCheck } from '../services/api';
import { mergeProduceData } from '../services/adapter';
import {
  calculateHistoryStats,
  createPurchaseRecord,
  loadPurchaseHistory,
  savePurchaseHistory,
} from '../services/transactions';

interface AppContextType {
  currentScreen: Screen;
  setCurrentScreen: (screen: Screen) => void;
  selectedProduce: ProduceItem;
  setSelectedProduce: (item: ProduceItem) => void;
  selectProduceById: (id: string, imageBase64?: string) => void;
  vendorAskingPrice: number;
  setVendorAskingPrice: React.Dispatch<React.SetStateAction<number>>;
  negotiationState: NegotiationState;
  setNegotiationLanguage: (language: NegotiationLanguage) => void;
  purchaseHistory: PurchaseRecord[];
  totalSavings: number;
  recordPurchase: (paidPrice: number) => void;
  selectedLocation: MandiLocation;
  setSelectedLocation: (loc: MandiLocation) => void;
  theme: AppTheme;
  setTheme: (t: AppTheme) => void;
  toggleTheme: () => void;
  isDrawerOpen: boolean;
  setIsDrawerOpen: (open: boolean) => void;
  isAudioModalOpen: boolean;
  setIsAudioModalOpen: (open: boolean) => void;
  isScanning: boolean;
  apiError: string | null;
  setApiError: (err: string | null) => void;
  capturedImage: string | null;
  allProduce: ProduceItem[];
  triggerCelebration: () => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

const DEFAULT_NEGOTIATION_LANGUAGE: NegotiationLanguage = 'hi';

const createInitialNegotiationState = (vendorAskingPrice: number): NegotiationState => ({
  status: 'idle',
  language: DEFAULT_NEGOTIATION_LANGUAGE,
  vendorAskingPrice,
  latestVendorCounterOffer: null,
  userCurrentOffer: null,
  recommendedNextOffer: null,
  error: null,
  lastUpdatedAt: null,
});

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentScreen, setCurrentScreen] = useState<Screen>('home');
  const [selectedProduce, setSelectedProduce] = useState<ProduceItem>(PRODUCE_DATABASE[0]);
  const [vendorAskingPrice, setVendorAskingPrice] = useState<number>(45);
  const [negotiationState, setNegotiationState] = useState<NegotiationState>(() => createInitialNegotiationState(45));
  const [purchaseHistory, setPurchaseHistory] = useState<PurchaseRecord[]>(() => loadPurchaseHistory());
  const [selectedLocation, setSelectedLocation] = useState<MandiLocation>(MANDI_LOCATIONS[0]);
  const [theme, setTheme] = useState<AppTheme>('terracotta');
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);
  const [isAudioModalOpen, setIsAudioModalOpen] = useState<boolean>(false);
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const haggleRequestIdRef = React.useRef(0);
  const historyStats = React.useMemo(() => calculateHistoryStats(purchaseHistory), [purchaseHistory]);
  const totalSavings = historyStats.totalSavings;

  const setVendorPriceAndMarkListening = React.useCallback<React.Dispatch<React.SetStateAction<number>>>((value) => {
    setVendorAskingPrice((previousPrice) => {
      const nextRaw = typeof value === 'function' ? value(previousPrice) : value;
      const nextPrice = Math.max(1, Math.round(Number(nextRaw) || 1));

      if (nextPrice !== previousPrice) {
        setNegotiationState((previous) => ({
          ...previous,
          status: 'listening',
          vendorAskingPrice: nextPrice,
          latestVendorCounterOffer: nextPrice,
          error: null,
          lastUpdatedAt: Date.now(),
        }));
      }

      return nextPrice;
    });
  }, []);

  const setNegotiationLanguage = React.useCallback((language: NegotiationLanguage) => {
    setNegotiationState((previous) => ({
      ...previous,
      language,
      status: 'processing',
      error: null,
      lastUpdatedAt: Date.now(),
    }));
  }, []);

  const selectProduceById = async (id: string, imageBase64?: string) => {
    setIsScanning(true);
    setApiError(null);
    if (imageBase64) {
      setCapturedImage(imageBase64);
    } else {
      setCapturedImage(null);
    }
    const fallbackItem = PRODUCE_DATABASE.find(p => p.id === id) || PRODUCE_DATABASE[0];
    try {
      const backendResponse = await fetchScanResult(fallbackItem.id, imageBase64);
      const finalId = backendResponse.detected_produce_id || fallbackItem.id;
      let detectedItem = PRODUCE_DATABASE.find(p => p.id === finalId);
      
      if (!detectedItem) {
        // If Gemini detects something not in our DB, use the 'unknown' generic template
        detectedItem = PRODUCE_DATABASE.find(p => p.id === 'unknown') || PRODUCE_DATABASE[0];
        // Inject the actual capitalized name from the backend (e.g. "Peanut")
        detectedItem = { ...detectedItem, name: backendResponse.produce_type || 'Unknown' };
      }
      
      const mergedItem = mergeProduceData(detectedItem, backendResponse);
      setSelectedProduce(mergedItem);
      setVendorAskingPrice(mergedItem.typicalVendorAsking);
      setNegotiationState((previous) => ({
        ...createInitialNegotiationState(mergedItem.typicalVendorAsking),
        language: previous.language,
      }));
      setCurrentScreen('quality_result');
    } catch (e) {
      console.error('API failed:', e);
      setApiError('Failed to connect to the server. Please check your connection and try again.');
    } finally {
      setIsScanning(false);
    }
  };

  useEffect(() => {
    if (!['quality_result', 'price_breakdown', 'bargain'].includes(currentScreen)) {
      return;
    }

    let activeController: AbortController | null = null;

    const verifyPrice = async () => {
      const requestId = ++haggleRequestIdRef.current;
      const controller = new AbortController();
      activeController = controller;
      const timeoutId = window.setTimeout(() => controller.abort(), 10000);

      try {
        setNegotiationState((previous) => ({
          ...previous,
          status: 'processing',
          vendorAskingPrice,
          latestVendorCounterOffer: vendorAskingPrice,
          error: null,
          lastUpdatedAt: Date.now(),
        }));

        const result = await fetchHaggleCheck(
          selectedProduce.name,
          vendorAskingPrice,
          selectedProduce.retailFairMin,
          selectedProduce.retailFairMax,
          selectedProduce.freshness,
          selectedProduce.quickCommercePrice,
          negotiationState.language,
          controller.signal
        );

        if (requestId !== haggleRequestIdRef.current) {
          return;
        }

        setSelectedProduce(prev => ({ 
          ...prev, 
          suggestedOfferPrice: result.suggested_price,
          haggleVerdict: result.verdict,
          haggleReasoning: result.reasoning,
          hagglePhrases: result.phrases,
          decision: result.decision,
          severity: result.severity,
          recommendation: result.recommendation,
          alternatives: result.alternatives,
          startingOffer: result.starting_offer,
          targetPrice: result.target_price,
          maximumReasonablePrice: result.maximum_reasonable_price,
          potentialSaving: result.potential_saving,
          belowFairAmount: result.below_fair_amount,
          qualityContext: result.quality_context,
        }));
        setNegotiationState((previous) => ({
          ...previous,
          status: 'ready',
          vendorAskingPrice,
          latestVendorCounterOffer: vendorAskingPrice,
          userCurrentOffer: result.starting_offer ?? result.suggested_price,
          recommendedNextOffer: result.target_price ?? result.suggested_price,
          error: null,
          lastUpdatedAt: Date.now(),
        }));
      } catch (e) {
        if (requestId !== haggleRequestIdRef.current) {
          return;
        }

        const isAbort = e instanceof DOMException && e.name === 'AbortError';
        console.error('Haggle check API failed:', e);
        setNegotiationState((previous) => ({
          ...previous,
          status: isAbort ? 'timeout' : 'error',
          error: isAbort
            ? 'Price check is taking longer than expected. Try again in a moment.'
            : 'Could not update the negotiation advice. The last recommendation is still shown.',
          lastUpdatedAt: Date.now(),
        }));
      } finally {
        window.clearTimeout(timeoutId);
      }
    };

    const debounceId = window.setTimeout(verifyPrice, 350);

    return () => {
      window.clearTimeout(debounceId);
      activeController?.abort();
      haggleRequestIdRef.current += 1;
    };
  }, [
    currentScreen,
    vendorAskingPrice,
    selectedProduce.name,
    selectedProduce.retailFairMin,
    selectedProduce.retailFairMax,
    selectedProduce.freshness,
    selectedProduce.quickCommercePrice,
    negotiationState.language,
  ]);

  useEffect(() => {
    savePurchaseHistory(purchaseHistory);
  }, [purchaseHistory]);

  const triggerCelebration = () => {
    try {
      confetti({
        particleCount: 50,
        spread: 65,
        origin: { y: 0.7 },
        colors: theme === 'terracotta' ? ['#9e3d00', '#ffb595', '#7bf8a1', '#ffdbcd'] : ['#0e6c4a', '#a0f4c8', '#1b4332', '#95D5B2']
      });
    } catch {
      // fallback if canvas confetti isn't supported
    }
  };

  const recordPurchase = (paidPrice: number) => {
    const newRecord = createPurchaseRecord({
      produce: selectedProduce,
      vendorAskingPrice,
      finalPaidPrice: paidPrice,
    });

    setPurchaseHistory(prev => [newRecord, ...prev]);
    triggerCelebration();
  };

  const toggleTheme = () => {
    setTheme(prev => (prev === 'terracotta' ? 'forest_green' : 'terracotta'));
  };

  // Scroll to top on screen change
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' });
  }, [currentScreen]);

  return (
    <AppContext.Provider
      value={{
        currentScreen,
        setCurrentScreen,
        selectedProduce,
        setSelectedProduce,
        selectProduceById,
        vendorAskingPrice,
        setVendorAskingPrice: setVendorPriceAndMarkListening,
        negotiationState,
        setNegotiationLanguage,
        purchaseHistory,
        totalSavings,
        recordPurchase,
        selectedLocation,
        setSelectedLocation,
        theme,
        setTheme,
        toggleTheme,
        isDrawerOpen,
        setIsDrawerOpen,
        isAudioModalOpen,
        setIsAudioModalOpen,
        isScanning,
        apiError,
        setApiError,
        capturedImage,
        allProduce: PRODUCE_DATABASE,
        triggerCelebration
      }}
    >
      <div className={theme === 'forest_green' ? 'theme-forest' : 'theme-terracotta'}>
        {children}
      </div>
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
