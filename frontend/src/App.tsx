import { useState } from 'react';
import { Shield, Loader2, RefreshCcw } from 'lucide-react';
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
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

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
      setErrorMessage(msg || 'Failed to analyze document. Make sure the server is running.');
      setAppState('error');
    }
  };

  const handleReset = () => {
    setAppState('idle');
    setFile(null);
    setAnalysisResult(null);
    setErrorMessage(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 text-blue-600">
            <Shield className="w-7 h-7" strokeWidth={2.5} />
            <h1 className="text-xl font-bold tracking-tight text-slate-900">TamperTrace</h1>
          </div>
          {appState === 'results' && (
            <button 
              onClick={handleReset}
              className="flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors bg-slate-100 hover:bg-slate-200 px-4 py-2 rounded-lg"
            >
              <RefreshCcw className="w-4 h-4" />
              New Analysis
            </button>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {appState === 'idle' && (
          <div className="max-w-2xl mx-auto text-center space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="space-y-4">
              <h2 className="text-4xl font-bold tracking-tight text-slate-900">
                Verify Document Authenticity
              </h2>
              <p className="text-lg text-slate-600 max-w-xl mx-auto">
                Upload identity cards, certificates, or invoices. Our AI ensemble analyzes pixels, metadata, and typography to detect manipulation.
              </p>
            </div>
            
            <UploadZone onFileSelect={handleFileSelect} isLoading={false} />
          </div>
        )}

        {(appState === 'uploading' || appState === 'analyzing') && (
          <div className="max-w-xl mx-auto text-center mt-20 animate-in fade-in duration-500">
            <div className="relative inline-flex items-center justify-center">
              <div className="absolute inset-0 bg-blue-100 rounded-full blur-xl opacity-50 animate-pulse" />
              <div className="relative bg-white p-4 rounded-2xl shadow-sm border border-slate-100">
                <Loader2 className="w-12 h-12 text-blue-500 animate-spin" strokeWidth={2} />
              </div>
            </div>
            <h3 className="mt-8 text-xl font-semibold text-slate-900">
              {appState === 'uploading' ? 'Uploading document...' : 'Running Forensic Analysis...'}
            </h3>
            <p className="mt-2 text-slate-500">
              {appState === 'analyzing' && 'Fusing ELA, TruFor, Copy-Move, EXIF, and OCR signals.'}
            </p>
          </div>
        )}

        {appState === 'error' && (
          <div className="max-w-xl mx-auto mt-12 animate-in fade-in slide-in-from-top-4">
            <div className="bg-rose-50 border border-rose-200 rounded-2xl p-8 text-center">
              <div className="bg-white w-16 h-16 rounded-full flex items-center justify-center mx-auto shadow-sm mb-6">
                <Shield className="w-8 h-8 text-rose-500" strokeWidth={2} />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-2">Analysis Failed</h3>
              <p className="text-rose-700 mb-8">{errorMessage}</p>
              <button 
                onClick={handleReset}
                className="bg-rose-600 hover:bg-rose-700 text-white font-medium px-6 py-2.5 rounded-lg transition-colors shadow-sm"
              >
                Try Again
              </button>
            </div>
          </div>
        )}

        {appState === 'results' && analysisResult && (
          <div className="space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-700">
            <div className="flex flex-col md:flex-row gap-8 items-start">
              {/* Left Column: Summary */}
              <div className="w-full md:w-1/3 space-y-8 sticky top-24">
                <VerdictBadge 
                  verdict={(analysisResult as any).pages[0].verdict} 
                  confidence={(analysisResult as any).pages[0].confidence_pct} 
                />
                
                <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
                  <h3 className="font-semibold text-slate-900 mb-2 text-lg">Document Info</h3>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between border-b border-slate-100 pb-2">
                      <span className="text-slate-500">Filename</span>
                      <span className="font-medium text-slate-900 truncate max-w-[150px]" title={String((analysisResult as any).filename)}>
                        {String((analysisResult as any).filename)}
                      </span>
                    </div>
                    <div className="flex justify-between border-b border-slate-100 pb-2">
                      <span className="text-slate-500">Pages</span>
                      <span className="font-medium text-slate-900">{String((analysisResult as any).total_pages)}</span>
                    </div>
                    <div className="flex justify-between pb-1">
                      <span className="text-slate-500">Fused Score</span>
                      <span className="font-medium text-slate-900">{Number((analysisResult as any).pages[0].fused_score).toFixed(3)}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Column: Deep Dive */}
              <div className="w-full md:w-2/3 space-y-12">
                <HeatmapOverlay 
                  originalImageSrc={previewUrl} 
                  heatmapBase64={(analysisResult as any).pages[0].heatmap_base64}
                  isPdf={file?.type === 'application/pdf'}
                />
                
                <SignalBreakdown signals={(analysisResult as any).pages[0].signals} />
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 mt-auto">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 text-center">
          <p className="text-sm font-medium text-slate-500">
            Automated analysis, not a certified forensic or legal opinion.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
