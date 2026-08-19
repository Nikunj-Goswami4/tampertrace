import { useState } from 'react';
import { Layers } from 'lucide-react';
import { cn } from '../utils';

interface HeatmapOverlayProps {
  originalImageSrc: string | null;
  heatmapBase64: string | null;
  isPdf?: boolean;
}

export function HeatmapOverlay({ originalImageSrc, heatmapBase64, isPdf }: HeatmapOverlayProps) {
  const [showHeatmap, setShowHeatmap] = useState(true);

  const heatmapSrc = heatmapBase64 ? `data:image/png;base64,${heatmapBase64}` : null;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
          <Layers className="w-5 h-5 text-blue-500" />
          Localization Heatmap
        </h3>
        
        {heatmapSrc && !isPdf && (
          <label className="flex items-center gap-3 cursor-pointer group">
            <span className="text-sm font-medium text-slate-600 group-hover:text-slate-900 transition-colors">
              Show Tamper Map
            </span>
            <div className="relative inline-flex items-center h-6 rounded-full w-11 transition-colors bg-slate-200">
              <input 
                type="checkbox" 
                className="sr-only peer"
                checked={showHeatmap}
                onChange={(e) => setShowHeatmap(e.target.checked)}
              />
              <div className={cn(
                "w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer transition-colors",
                "peer-checked:after:translate-x-full peer-checked:after:border-white after:content-['']",
                "after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300",
                "after:border after:rounded-full after:h-5 after:w-5 after:transition-all",
                "peer-checked:bg-blue-500"
              )}></div>
            </div>
          </label>
        )}
      </div>

      <div className="relative w-full max-w-4xl mx-auto rounded-xl overflow-hidden bg-slate-100 border border-slate-200 shadow-sm flex items-center justify-center min-h-[300px]">
        {/* Base Image (if not PDF) */}
        {!isPdf && originalImageSrc && (
          <img 
            src={originalImageSrc} 
            alt="Original document" 
            className="w-full h-auto object-contain max-h-[70vh]"
          />
        )}
        
        {/* PDF Placeholder if no heatmap */}
        {isPdf && !heatmapSrc && (
          <div className="p-8 text-center text-slate-500">
            PDF Document Analyzed. No heatmap generated.
          </div>
        )}

        {/* Heatmap Overlay */}
        {heatmapSrc && (
          <img 
            src={heatmapSrc} 
            alt="Tamper Heatmap" 
            className={cn(
              "w-full h-auto object-contain max-h-[70vh] transition-opacity duration-300",
              (!isPdf && originalImageSrc) ? "absolute inset-0" : "relative",
              (!isPdf && !showHeatmap) ? "opacity-0" : "opacity-80 mix-blend-multiply"
            )}
          />
        )}

        {!heatmapSrc && !isPdf && originalImageSrc && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/50 backdrop-blur-sm">
            <span className="bg-white px-4 py-2 rounded-full text-sm font-medium text-slate-600 shadow-sm">
              No anomaly heatmap available for this document
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
