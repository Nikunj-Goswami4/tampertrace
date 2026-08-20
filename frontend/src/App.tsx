import { useState, useEffect, useRef } from 'react';
import { Shield, RefreshCcw, Moon, Sun, Download } from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadZone } from './components/UploadZone';
import { VerdictBadge } from './components/VerdictBadge';
import { HeatmapOverlay } from './components/HeatmapOverlay';
import { SignalBreakdown } from './components/SignalBreakdown';

type AppState = 'idle' | 'uploading' | 'analyzing' | 'results' | 'error';

function App() {
  const [appState, setAppState] = useState<AppState>('idle');
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<Record<string, unknown> | null>(null);

  // Use user's system preference or default to true for "cinematic dark mode"
  const [isDarkMode, setIsDarkMode] = useState(true);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  const handleDownloadPdf = () => {
    // Force light mode for a clean, legible PDF report
    const wasDark = document.documentElement.classList.contains('dark');
    if (wasDark) {
      document.documentElement.classList.remove('dark');
      setIsDarkMode(false);
    }
    
    // Give the DOM a moment to re-render without dark mode classes
    setTimeout(() => {
      window.print();
      // Restore dark mode if it was active
      if (wasDark) {
        document.documentElement.classList.add('dark');
        setIsDarkMode(true);
      }
    }, 150);
  };
  const handleFileSelect = async (selectedFile: File) => {
    setFile(selectedFile);
    if (selectedFile.type.startsWith('image/')) {
      setPreviewUrl(URL.createObjectURL(selectedFile));
    } else {
      setPreviewUrl(null);
    }

    setAppState('uploading');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      setAppState('analyzing');
      const response = await fetch('http://127.0.0.1:8000/api/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        let errStr = 'An unknown error occurred.';
        try {
          const errData = await response.json();
          errStr = errData.detail || errStr;
        } catch {
          errStr = `Server responded with status ${response.status}`;
        }
        throw new Error(errStr);
      }

      const data = await response.json();
      setAnalysisResult(data);
      setAppState('results');
    } catch (error: unknown) {
      console.error(error);
      const msg = error instanceof Error ? error.message : 'An unknown error occurred.';
      toast.error(msg || 'Failed to analyze document. Make sure the server is running.');
      setAppState('idle');
    }
  };

  const handleReset = () => {
    setAppState('idle');
    setFile(null);
    setAnalysisResult(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col font-sans transition-colors duration-300">
      <Toaster position="bottom-right" toastOptions={{ className: 'dark:bg-slate-800 dark:text-white' }} />
      {/* Header */}
      <header className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 sticky top-0 z-10 transition-colors duration-300">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 text-blue-600 dark:text-blue-500">
            <Shield className="w-7 h-7" strokeWidth={2.5} />
            <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white transition-colors duration-300">TamperTrace</h1>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setIsDarkMode(!isDarkMode)}
              className="p-2 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white transition-colors rounded-full hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              {isDarkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
            {appState === 'results' && (
              <>
                <button
                  onClick={handleDownloadPdf}
                  className="hidden sm:flex items-center gap-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 px-4 py-2 rounded-lg"
                >
                  <Download className="w-4 h-4" />
                  Download Report
                </button>
                <button
                  onClick={handleReset}
                  className="flex items-center gap-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 px-4 py-2 rounded-lg"
                >
                  <RefreshCcw className="w-4 h-4" />
                  New Analysis
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12" ref={contentRef}>
        <AnimatePresence mode="wait">
          {appState === 'idle' && (
            <motion.div
              key="idle"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95, y: -20 }}
              transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
              className="max-w-2xl mx-auto text-center space-y-8"
            >
              <div className="space-y-4">
                <h2 className="text-4xl font-bold tracking-tight text-slate-900 dark:text-white transition-colors duration-300">
                  Verify Document Authenticity
                </h2>
                <p className="text-lg text-slate-600 dark:text-slate-400 max-w-xl mx-auto transition-colors duration-300">
                  Upload identity cards, certificates, or invoices. Our AI ensemble analyzes pixels, metadata, and typography to detect manipulation.
                </p>
              </div>

              <UploadZone onFileSelect={handleFileSelect} isLoading={false} />
            </motion.div>
          )}

          {(appState === 'uploading' || appState === 'analyzing') && (
            <motion.div
              key="loading"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.5 }}
              className="max-w-xl mx-auto text-center mt-20"
            >
              {/* Immersive Scanning Laser Loading State */}
              <div className="relative w-48 h-64 mx-auto bg-slate-200 dark:bg-slate-800 rounded-lg overflow-hidden border border-slate-300 dark:border-slate-700 shadow-inner transition-colors duration-300">
                {previewUrl ? (
                  <img src={previewUrl} className="w-full h-full object-cover opacity-50 grayscale" alt="preview" />
                ) : (
                  <div className="w-full h-full p-4 flex flex-col gap-3">
                    <div className="w-full h-4 bg-slate-300 dark:bg-slate-700 rounded animate-pulse"></div>
                    <div className="w-3/4 h-4 bg-slate-300 dark:bg-slate-700 rounded animate-pulse"></div>
                    <div className="w-full h-24 bg-slate-300 dark:bg-slate-700 rounded mt-auto animate-pulse"></div>
                  </div>
                )}
                {/* Laser line */}
                <motion.div
                  className="absolute top-0 left-0 w-full h-1 bg-blue-500 shadow-[0_0_15px_3px_rgba(59,130,246,0.8)]"
                  animate={{ top: ['0%', '100%', '0%'] }}
                  transition={{ duration: 2.5, repeat: Infinity, ease: 'linear' }}
                />
              </div>

              <motion.h3
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="mt-8 text-xl font-semibold text-slate-900 dark:text-white transition-colors duration-300"
              >
                {appState === 'uploading' ? 'Uploading document...' : 'Running Forensic Analysis...'}
              </motion.h3>
              <p className="mt-2 text-slate-500 dark:text-slate-400 transition-colors duration-300">
                {appState === 'analyzing' && 'Fusing ELA, TruFor, Copy-Move, EXIF, and OCR signals.'}
              </p>
            </motion.div>
          )}

          {appState === 'results' && analysisResult && (
            <motion.div
              key="results"
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              className="space-y-12"
            >
              <div className="flex flex-col gap-16">
                {(analysisResult as any).pages.slice(0, 3).map((pageData: any, idx: number) => (
                  <div key={idx} className="flex flex-col md:flex-row gap-8 items-start relative">
                    {/* Left Column: Summary */}
                    <div className="w-full md:w-1/3 space-y-8 md:sticky md:top-24">
                      {((analysisResult as any).total_pages > 1) && (
                        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
                          Page {idx + 1}
                        </h2>
                      )}
                      <VerdictBadge
                        verdict={pageData.verdict}
                        confidence={pageData.confidence_pct}
                      />

                      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm transition-colors duration-300">
                        <h3 className="font-semibold text-slate-900 dark:text-white mb-2 text-lg">
                          {((analysisResult as any).total_pages > 1) ? `Page ${idx + 1} Info` : 'Document Info'}
                        </h3>
                        <div className="space-y-3 text-sm">
                          {idx === 0 && (
                            <>
                              <div className="flex justify-between border-b border-slate-100 dark:border-slate-700/50 pb-3 gap-4">
                                <span className="text-slate-500 dark:text-slate-400 shrink-0">Filename</span>
                                <span className="font-medium text-slate-900 dark:text-slate-200 break-all text-right" title={String((analysisResult as any).filename)}>
                                  {String((analysisResult as any).filename)}
                                </span>
                              </div>
                              <div className="flex justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
                                <span className="text-slate-500 dark:text-slate-400">Total Pages</span>
                                <span className="font-medium text-slate-900 dark:text-slate-200">{String((analysisResult as any).total_pages)}</span>
                              </div>
                            </>
                          )}
                          <div className="flex justify-between pb-1">
                            <span className="text-slate-500 dark:text-slate-400">Fused Score</span>
                            <span className="font-medium text-slate-900 dark:text-slate-200">{Number(pageData.fused_score).toFixed(3)}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Right Column: Deep Dive */}
                    <div className="w-full md:w-2/3 space-y-12">
                      <HeatmapOverlay
                        originalImageSrc={pageData.original_image_b64 ? `data:image/jpeg;base64,${pageData.original_image_b64}` : previewUrl}
                        heatmapBase64={pageData.heatmap_base64}
                        isPdf={file?.type === 'application/pdf'}
                      />

                      <SignalBreakdown signals={pageData.signals} />
                    </div>
                  </div>
                ))}

                {((analysisResult as any).total_pages > 3) && (
                  <div className="text-center p-6 bg-slate-100 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-800 mt-8">
                    <p className="text-slate-600 dark:text-slate-400 font-medium">
                      Showing the first 3 pages of {(analysisResult as any).total_pages} total pages to keep the report concise.
                    </p>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Footer */}
      <footer className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-t border-slate-200 dark:border-slate-800 mt-auto transition-colors duration-300">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 text-center">
          <p className="text-sm font-medium text-slate-500 dark:text-slate-500">
            Automated analysis, not a certified forensic or legal opinion.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
