import React, { createContext, useContext, useState, useEffect } from 'react';
import { Screen, ProduceItem, PurchaseRecord, MandiLocation, AppTheme, PurchaseType } from '../types';
import { PRODUCE_DATABASE, INITIAL_PURCHASE_HISTORY } from '../data/produceData';
import { MANDI_LOCATIONS } from '../data/mandiLocations';
import confetti from 'canvas-confetti';
import { fetchScanResult, fetchHaggleCheck } from '../services/api';
import { mergeProduceData } from '../services/adapter';
import { SECTOR_OPTIONS, FOOD_SECTOR_ID, FRESH_PRODUCE_COMPONENT } from '../data/sectorData';

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
  vendorAskingPrice: number;
  setVendorAskingPrice: React.Dispatch<React.SetStateAction<number>>;
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
  const [apiError, setApiError] = useState<string | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);

  const selectedSectorName = SECTOR_OPTIONS.find((sector) => sector.id === selectedSectorId)?.name || '';

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
      const backendResponse = await fetchScanResult(fallbackItem.id, imageBase64, {
        state: selectedLocation.state,
        district: selectedLocation.name.split(', ').pop(),
        market: selectedLocation.mandiName,
        purchase_type: purchaseType || 'street_vendor',
      });
      const finalId = backendResponse.detected_produce_id || fallbackItem.id;
      let detectedItem = PRODUCE_DATABASE.find(p => p.id === finalId);
      
      if (!detectedItem) {
        // If Gemini detects something not in our DB, use the 'unknown' generic template
        detectedItem = PRODUCE_DATABASE.find(p => p.id === 'unknown') || PRODUCE_DATABASE[0];
        // Inject the actual capitalized name from the backend (e.g. "Peanut")
        detectedItem = { ...detectedItem, name: backendResponse.produce_type || 'Unknown' };
      }
      
      const mergedItem = mergeProduceData(detectedItem, backendResponse);
      if (mergedItem.retailFairMin > 0 && mergedItem.retailFairMax > 0) {
        try {
          const haggle = await fetchHaggleCheck(mergedItem.typicalVendorAsking, mergedItem.retailFairMin, mergedItem.retailFairMax);
          mergedItem.suggestedOfferPrice = haggle.suggested_price;
        } catch (haggleError) {
          console.error('Initial haggle calculation failed:', haggleError);
        }
      }
      setSelectedProduce(mergedItem);
      setVendorAskingPrice(mergedItem.typicalVendorAsking);
      setCurrentScreen('quality_result');
    } catch (e) {
      console.error('API failed:', e);
      setApiError('Failed to connect to the server. Please check your connection and try again.');
    } finally {
      setIsScanning(false);
    }
  };

  useEffect(() => {
    const verifyPrice = async () => {
      try {
        if (!selectedProduce.retailFairMin || !selectedProduce.retailFairMax) return;
        const result = await fetchHaggleCheck(vendorAskingPrice, selectedProduce.retailFairMin, selectedProduce.retailFairMax);
        setSelectedProduce(prev => ({ ...prev, suggestedOfferPrice: result.suggested_price }));
      } catch (e) {
        console.error('Haggle check API failed:', e);
        // We might not want a blocking error for just the haggle check update, but we can log it.
      }
    };
    verifyPrice();
  }, [vendorAskingPrice]);

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
    // calculate savings vs fair average
    const fairAvg = Math.round((selectedProduce.retailFairMin + selectedProduce.retailFairMax) / 2);
    const vendorDiff = vendorAskingPrice - paidPrice;
    const actualSaved = vendorDiff > 0 ? vendorDiff : Math.max(0, fairAvg - paidPrice);

    const newRecord: PurchaseRecord = {
      id: 'rec-' + Date.now(),
      produceId: selectedProduce.id,
      produceName: selectedProduce.name,
      paidPrice: paidPrice,
      fairPrice: fairAvg,
      savedAmount: actualSaved,
      date: 'Just now',
      timestamp: Date.now(),
      iconType: (selectedProduce.id === 'tomato' || selectedProduce.id === 'onion' || selectedProduce.id === 'potato')
        ? (selectedProduce.id as 'tomato' | 'onion' | 'potato')
        : 'general'
    };

    setPurchaseHistory(prev => [newRecord, ...prev]);
    setTotalSavings(prev => prev + actualSaved);
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
