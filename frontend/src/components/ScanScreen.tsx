import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../context/AppContext';

export const ScanScreen: React.FC = () => {
  const { setCurrentScreen, selectedProduce, selectProduceById, theme } = useApp();
  const [flashOn, setFlashOn] = useState(false);
  const [isScanning, setIsScanning] = useState(true);
  const [useRealCamera, setUseRealCamera] = useState(true);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const isTerracotta = theme === 'terracotta';

  // Handle Real Camera stream
  useEffect(() => {
    let stream: MediaStream | null = null;
    if (useRealCamera && navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      setCameraError(null);
      navigator.mediaDevices
        .getUserMedia({ video: { facingMode: 'environment' } })
        .then((s) => {
          stream = s;
          if (videoRef.current) {
            videoRef.current.srcObject = s;
          }
        })
        .catch((err) => {
          console.error('Camera access denied:', err);
          setCameraError('Camera access was denied or is unavailable.');
        });
    }

    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [useRealCamera]);

  // Auto-scan timer simulation (3 seconds then transition to quality result)
  useEffect(() => {
    // Only auto-scan in simulation mode, real camera requires manual capture
    if (!isScanning || useRealCamera) return;
    const timer = setTimeout(() => {
      handleCompleteScan();
    }, 3200);

    return () => clearTimeout(timer);
  }, [isScanning, selectedProduce, useRealCamera]);

  const handleCompleteScan = () => {
    // Haptic feedback
    if (navigator.vibrate) navigator.vibrate(60);

    if (!useRealCamera) {
      return;
    }
    
    let base64Image = undefined;
    if (useRealCamera && videoRef.current) {
      const canvas = document.createElement('canvas');
      canvas.width = videoRef.current.videoWidth || 640;
      canvas.height = videoRef.current.videoHeight || 480;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
        base64Image = canvas.toDataURL('image/jpeg', 0.8);
      }
    }
    
    // Send the captured frame to the backend for identification and freshness scoring.
    selectProduceById(selectedProduce.id, base64Image);
  };

  const handleToggleFlash = () => {
    setFlashOn(!flashOn);
    if (navigator.vibrate) navigator.vibrate(25);
  };

  return (
    <div
      id="scan-viewfinder-screen"
      className="fixed inset-0 z-50 w-screen h-[100dvh] overflow-hidden bg-black flex flex-col justify-between select-none"
    >
      {/* Background Image / Camera Feed */}
      {useRealCamera ? (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="absolute inset-0 w-full h-full object-cover z-0"
        />
      ) : (
        <div
          className="absolute inset-0 z-0 bg-cover bg-center transition-all duration-700"
          style={{
            backgroundImage: `url('https://lh3.googleusercontent.com/aida-public/AB6AXuCkzUwqgkVvCn6E60HTA8TOXBs9-xQzClnZGuhxfmZuNkqaEv2YrmOhhu7T7czgA-lobmVGXiHPqnJJBO7cI0E4DmB30ym7OxaWUx0HcqBiJ7keGtTW7JQKhdrb0XaiCaJgOfznnhxyCc4xFQY8ybmP9fHuUaJUevkhcdgsmjnuX29oaGBvV_jGnJUg7FglFzWhdpgN3oRL3NCVkkSID7v2vEieJsTx2NggoUpF8rLYhfwgZ06SZ93T-w')`,
            filter: flashOn ? 'brightness(1.4) contrast(1.1)' : 'brightness(0.95)'
          }}
        />
      )}

      {/* Dim overlay */}
      <div className="absolute inset-0 z-0 bg-black/25 pointer-events-none" />

      {/* Camera Error Overlay */}
      {cameraError && (
        <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-black/80 p-6 text-center">
          <span className="material-symbols-outlined text-[48px] text-red-500 mb-4">videocam_off</span>
          <p className="text-white font-medium mb-6">{cameraError}</p>
          <button
            onClick={() => {
              setCameraError(null);
              setUseRealCamera(false);
            }}
            className="px-6 py-3 rounded-full bg-white text-black font-semibold active:scale-95 transition-all"
          >
            Use Market Simulation Instead
          </button>
        </div>
      )}

      {/* Flash simulation glare if on */}
      {flashOn && (
        <div className="absolute inset-0 z-1 bg-white/20 pointer-events-none transition-opacity duration-200" />
      )}

      {/* Top Header Bar */}
      <header className="relative z-20 flex justify-between items-center px-5 pt-6 pb-2 w-full">
        {/* Close Button */}
        <button
          id="scanner-close-btn"
          aria-label="Close Scanner"
          onClick={() => setCurrentScreen('home')}
          className="w-12 h-12 flex items-center justify-center rounded-full bg-[#fbf9f5]/85 backdrop-blur-md text-[#1b1c1a] shadow-lg active:scale-90 transition-transform"
        >
          <span className="material-symbols-outlined text-[24px]">close</span>
        </button>

        {/* Quick Camera Mode Switcher (Simulated vs Live) */}
        <button
          onClick={() => setUseRealCamera(!useRealCamera)}
          className="px-3 py-1 rounded-full bg-black/40 backdrop-blur-md text-white text-[11px] font-medium border border-white/20 active:scale-95 transition-transform"
        >
          {useRealCamera ? '📷 Live Camera' : '🖼 Market Simulation'}
        </button>

        {/* Flash Toggle */}
        <button
          id="scanner-flash-btn"
          aria-label="Toggle Flash"
          onClick={handleToggleFlash}
          className={`w-12 h-12 flex items-center justify-center rounded-full backdrop-blur-md shadow-lg active:scale-90 transition-all ${
            flashOn
              ? isTerracotta
                ? 'bg-[#c64f00] text-white'
                : 'bg-[#1b4332] text-white'
              : 'bg-[#fbf9f5]/85 text-[#1b1c1a]'
          }`}
        >
          <span className="material-symbols-outlined text-[24px]">
            {flashOn ? 'flash_on' : 'flash_off'}
          </span>
        </button>
      </header>

      {/* Main Viewfinder Canvas */}
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-5">
        {/* Instructional Floating Pill */}
        <div
          id="scanner-instruction-pill"
          className="mb-8 bg-[#fbf9f5]/90 backdrop-blur-md px-6 py-3 rounded-full shadow-[0px_8px_24px_rgba(0,0,0,0.25)] border border-white/60 text-center animate-in fade-in slide-in-from-top-4 duration-300"
        >
          <p className={`font-display text-[18px] font-bold ${isTerracotta ? 'text-[#9e3d00]' : 'text-[#012d1d]'}`}>
            Point at the produce
          </p>
          <p className="text-[13px] text-[#594238] mt-0.5">
            Align the item within the frame
          </p>
        </div>

        {/* Scanning Reticle Frame */}
        <div id="scanner-reticle" className="relative w-72 h-72">
          {/* Animated Laser Scanning Line */}
          <div className="scanning-line z-20" />

          {/* Corner Markers */}
          {/* Top Left */}
          <div
            className={`absolute top-0 left-0 w-12 h-12 border-t-4 border-l-4 rounded-tl-2xl pulse-corner z-10 ${
              isTerracotta ? 'border-[#9e3d00]' : 'border-[#012d1d]'
            }`}
          />
          {/* Top Right */}
          <div
            className={`absolute top-0 right-0 w-12 h-12 border-t-4 border-r-4 rounded-tr-2xl pulse-corner z-10 ${
              isTerracotta ? 'border-[#9e3d00]' : 'border-[#012d1d]'
            }`}
          />
          {/* Bottom Left */}
          <div
            className={`absolute bottom-0 left-0 w-12 h-12 border-b-4 border-l-4 rounded-bl-2xl pulse-corner z-10 ${
              isTerracotta ? 'border-[#9e3d00]' : 'border-[#012d1d]'
            }`}
          />
          {/* Bottom Right */}
          <div
            className={`absolute bottom-0 right-0 w-12 h-12 border-b-4 border-r-4 rounded-br-2xl pulse-corner z-10 ${
              isTerracotta ? 'border-[#9e3d00]' : 'border-[#012d1d]'
            }`}
          />

          {/* Reticle Center Focus Hint */}
          <div className="absolute inset-0 flex items-center justify-center opacity-35 pointer-events-none">
            <span className="material-symbols-outlined text-white text-[72px]">
              center_focus_strong
            </span>
          </div>

          {/* Identification status pill */}
          <div className="absolute -bottom-5 left-1/2 -translate-x-1/2 bg-black/70 backdrop-blur-md px-3.5 py-1 rounded-full border border-white/20 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md">
            <span className="w-2 h-2 rounded-full bg-[#7bf8a1] animate-ping" />
            Ready to identify and score
          </div>
        </div>
      </main>

      {/* Bottom Manual Capture & Auto-scan status */}
      <footer className="relative z-20 pb-10 flex flex-col items-center justify-center">
        {/* Manual Trigger Button */}
        <button
          id="scanner-capture-btn"
          aria-label="Capture Produce"
          onClick={handleCompleteScan}
          className={`w-20 h-20 rounded-full flex items-center justify-center border-2 backdrop-blur-sm active:scale-90 transition-all duration-150 ${
            isTerracotta
              ? 'bg-[#9e3d00]/25 border-[#9e3d00]/60'
              : 'bg-[#012d1d]/25 border-[#012d1d]/60'
          }`}
        >
          <div
            className={`w-14 h-14 rounded-full shadow-[0px_4px_20px_rgba(0,0,0,0.4)] ${
              isTerracotta ? 'bg-[#9e3d00]' : 'bg-[#012d1d]'
            }`}
          />
        </button>

        <p className="text-[13px] font-medium text-white/95 text-center mt-3 drop-shadow-[0_2px_4px_rgba(0,0,0,0.8)] flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          {useRealCamera
            ? 'Capture a photo to identify and score'
            : 'Market Simulation: no real photo available'}
        </p>
      </footer>
    </div>
  );
};
