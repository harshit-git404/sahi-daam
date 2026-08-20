import React, { createContext, useContext, useState, useRef, useEffect } from 'react';
import { Screen, ProduceItem, PurchaseRecord, MandiLocation, AppTheme, PurchaseType } from '../types';
import { PRODUCE_DATABASE, INITIAL_PURCHASE_HISTORY } from '../data/produceData';
import { MANDI_LOCATIONS } from '../data/mandiLocations';
import confetti from 'canvas-confetti';
import { fetchScanResult } from '../services/api';
import { mergeProduceData } from '../services/adapter';
import { SECTOR_OPTIONS, FOOD_SECTOR_ID, FRESH_PRODUCE_COMPONENT } from '../data/sectorData';

/** Placeholder ProduceItem used while awaiting backend response */
const UNKNOWN_TEMPLATE: ProduceItem = {
  id: 'unknown',
  name: 'Unknown Produce',
  hindiName: 'Sabzi/Phal',
  image: 'https://images.unsplash.com/photo-1610832958506-aa56368176cf?auto=format&fit=crop&w=400&q=80',
  matchScore: 0,
  qualitySummary: '',
  freshness: 'fresh',
  freshnessPercent: 0,
  // Prices are intentionally 0 — must come from backend; never inherit catalog
  wholesalePrice: 0,
  markupMinPercent: 0,
  markupMaxPercent: 0,
  retailFairMin: 0,
  retailFairMax: 0,
  typicalVendorAsking: 0,
  suggestedOfferPrice: 0,
  unit: 'kg',
  qualityAdjustment: 0,
  qualityAdjustmentLabel: '',
  dataConfidence: 'Unavailable',
  category: 'Vegetables',
  bargainPhrases: [
    {
      hindi: 'भैया, सही दाम लगाइए, रोज़ का आना जाना है।',
      english: 'Please give a fair price, I am a regular customer.',
      phonetic: 'Bhaiya, sahi daam lagaiye, roz ka aana jaana hai.',
    },
  ],
};

interface AppContextType {
  currentScreen: Screen;
  setCurrentScreen: (screen: Screen) => void;
  selectedSectorId: string | null;
  selectedSectorName: string;
  selectedComponent: string | null;
  purchaseType: PurchaseType | null;
  setPurchaseType: (type: PurchaseType) => void;
  selectSector: (sectorId: string) => void;
  selectComponent: (component: string) => void;
  selectedProduce: ProduceItem;
  setSelectedProduce: (item: ProduceItem) => void;
  selectProduceById: (id: string, imageBase64?: string) => void;
  /** Set vendor asking price. Haggle is NOT recalculated automatically; call fetchHaggle explicitly. */
  vendorAskingPrice: number;
  setVendorAskingPrice: React.Dispatch<React.SetStateAction<number>>;
  /** Call this from BargainScreen only, after purchase type is confirmed as street_vendor */
  fetchHaggle: (askingPrice: number) => Promise<void>;
  haggleResult: { suggested_price: number; verdict: string; deviation_pct: number; explanation?: string } | null;
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
  isHaggling: boolean;
  apiError: string | null;
  setApiError: (err: string | null) => void;
  capturedImage: string | null;
  allProduce: ProduceItem[];
  triggerCelebration: () => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentScreen, setCurrentScreen] = useState<Screen>('home');
  const [selectedSectorId, setSelectedSectorId] = useState<string | null>(null);
  const [selectedComponent, setSelectedComponent] = useState<string | null>(null);
  const [purchaseType, setPurchaseType] = useState<PurchaseType | null>(null);
  const [selectedProduce, setSelectedProduce] = useState<ProduceItem>(PRODUCE_DATABASE[0]);
  const [vendorAskingPrice, setVendorAskingPrice] = useState<number>(45);
  const [purchaseHistory, setPurchaseHistory] = useState<PurchaseRecord[]>(INITIAL_PURCHASE_HISTORY);
  const [totalSavings, setTotalSavings] = useState<number>(340);
  const [selectedLocation, setSelectedLocation] = useState<MandiLocation>(MANDI_LOCATIONS[0]);
  const [theme, setTheme] = useState<AppTheme>('terracotta');
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);
  const [isAudioModalOpen, setIsAudioModalOpen] = useState<boolean>(false);
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [isHaggling, setIsHaggling] = useState<boolean>(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [haggleResult, setHaggleResult] = useState<AppContextType['haggleResult']>(null);

  // Ref to track the current scan request so stale results are discarded
  const scanRequestIdRef = useRef<number>(0);

  const selectedSectorName =
    SECTOR_OPTIONS.find((sector) => sector.id === selectedSectorId)?.name || '';

  const selectSector = (sectorId: string) => {
    setSelectedSectorId(sectorId);
    setSelectedComponent(null);
    setCurrentScreen('component_selection');
  };

  const selectComponent = (component: string) => {
    setSelectedComponent(component);
    if (selectedSectorId === FOOD_SECTOR_ID && component === FRESH_PRODUCE_COMPONENT) {
      setCurrentScreen('scan');
    } else {
      setCurrentScreen('sector_analysis');
    }
  };

  /**
   * Scan a produce item. This is the ONLY place the backend is called for ML/price analysis.
   * The haggle endpoint is NOT called here — it's triggered manually in BargainScreen.
   */
  const selectProduceById = async (id: string, imageBase64?: string) => {
    const requestId = ++scanRequestIdRef.current;
    setIsScanning(true);
    setApiError(null);
    setHaggleResult(null);
    setCapturedImage(imageBase64 ?? null);
    setPurchaseType(null); // reset purchase type for each new scan

    try {
      // Use structured location fields — no fragile string parsing
      const locationDistrict = selectedLocation.district
        || selectedLocation.name.split(',')[0].trim();
      const locationState = selectedLocation.state;
      const locationMarket = selectedLocation.mandiName;

      const backendResponse = await fetchScanResult(id, imageBase64, {
        state: locationState,
        district: locationDistrict,
        market: locationMarket,
        purchase_type: 'street_vendor', // scan always returns both; purchase type gates display
      });

      // Ignore stale responses if a new scan was started
      if (requestId !== scanRequestIdRef.current) return;

      // Resolve produce: use backend-detected ID, then catalog, then unknown template
      const detectedId: string =
        (backendResponse.detected_produce_id as string | undefined) || id;
      let catalogEntry = PRODUCE_DATABASE.find((p) => p.id === detectedId);

      if (!catalogEntry) {
        // Unknown produce: build from template with backend-supplied name
        // Prices come from backend ONLY — never inherit another produce's catalog prices
        catalogEntry = {
          ...UNKNOWN_TEMPLATE,
          name: String(backendResponse.produce_type || 'Unknown Produce'),
          id: detectedId,
        };
      }

      const mergedItem = mergeProduceData(catalogEntry, backendResponse);
      setSelectedProduce(mergedItem);

      // Seed vendor asking price from fair max + 15% (dynamic from backend)
      if (mergedItem.retailFairMax > 0) {
        setVendorAskingPrice(Math.round(mergedItem.retailFairMax * 1.15));
      } else {
        setVendorAskingPrice(mergedItem.typicalVendorAsking || 50);
      }

      setCurrentScreen('quality_result');
    } catch (err: unknown) {
      if (requestId !== scanRequestIdRef.current) return;
      console.error('[selectProduceById] Scan failed:', err);
      const message =
        err instanceof Error ? err.message : 'Could not connect to the server. Check your connection.';
      setApiError(message);
    } finally {
      if (requestId === scanRequestIdRef.current) {
        setIsScanning(false);
      }
    }
  };

  /**
   * Fetch haggle verdict from backend.
   * MUST only be called for street_vendor purchase type.
   * Called explicitly from BargainScreen when the user enters an asking price.
   */
  const fetchHaggle = async (askingPrice: number) => {
    if (purchaseType !== 'street_vendor') {
      console.warn('[fetchHaggle] Haggle is only available for street_vendor purchases.');
      return;
    }
    if (selectedProduce.retailFairMin <= 0 || selectedProduce.retailFairMax <= 0) {
      console.warn('[fetchHaggle] Market price unavailable; cannot compute haggle verdict.');
      return;
    }
    setIsHaggling(true);
    try {
      const { fetchHaggleCheck } = await import('../services/api');
      const result = await fetchHaggleCheck(
        askingPrice,
        selectedProduce.retailFairMin,
        selectedProduce.retailFairMax,
        {
          purchase_type: 'street_vendor',
          market_reference: selectedProduce.wholesalePrice || undefined,
          online_reference_min: selectedProduce.onlineReferenceMin ?? undefined,
          online_reference_max: selectedProduce.onlineReferenceMax ?? undefined,
        },
      );
      setHaggleResult({
        suggested_price: result.suggested_price,
        verdict: result.verdict,
        deviation_pct: result.deviation_pct,
        explanation: result.explanation,
      });
      // Also update suggestedOfferPrice on the produce item for display consistency
      setSelectedProduce((prev) => ({ ...prev, suggestedOfferPrice: result.suggested_price }));
    } catch (err: unknown) {
      console.error('[fetchHaggle] Haggle check failed:', err);
      // Don't block the UI — keep the client-side fair-range midpoint as fallback
    } finally {
      setIsHaggling(false);
    }
  };

  const triggerCelebration = () => {
    try {
      confetti({
        particleCount: 50,
        spread: 65,
        origin: { y: 0.7 },
        colors:
          theme === 'terracotta'
            ? ['#9e3d00', '#ffb595', '#7bf8a1', '#ffdbcd']
            : ['#0e6c4a', '#a0f4c8', '#1b4332', '#95D5B2'],
      });
    } catch {
      // confetti not supported
    }
  };

  const recordPurchase = (paidPrice: number) => {
    const fairAvg =
      selectedProduce.retailFairMin > 0 && selectedProduce.retailFairMax > 0
        ? Math.round((selectedProduce.retailFairMin + selectedProduce.retailFairMax) / 2)
        : 0;
    const vendorDiff = vendorAskingPrice - paidPrice;
    const actualSaved = vendorDiff > 0 ? vendorDiff : Math.max(0, fairAvg - paidPrice);

    const newRecord: PurchaseRecord = {
      id: 'rec-' + Date.now(),
      produceId: selectedProduce.id,
      produceName: selectedProduce.name,
      paidPrice,
      fairPrice: fairAvg,
      savedAmount: actualSaved,
      date: 'Just now',
      timestamp: Date.now(),
      iconType:
        selectedProduce.id === 'tomato' ||
        selectedProduce.id === 'onion' ||
        selectedProduce.id === 'potato'
          ? (selectedProduce.id as 'tomato' | 'onion' | 'potato')
          : 'general',
    };

    setPurchaseHistory((prev) => [newRecord, ...prev]);
    setTotalSavings((prev) => prev + actualSaved);
    triggerCelebration();
  };

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'terracotta' ? 'forest_green' : 'terracotta'));
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
        selectedSectorId,
        selectedSectorName,
        selectedComponent,
        purchaseType,
        setPurchaseType,
        selectSector,
        selectComponent,
        selectedProduce,
        setSelectedProduce,
        selectProduceById,
        vendorAskingPrice,
        setVendorAskingPrice,
        fetchHaggle,
        haggleResult,
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
        isHaggling,
        apiError,
        setApiError,
        capturedImage,
        allProduce: PRODUCE_DATABASE,
        triggerCelebration,
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
