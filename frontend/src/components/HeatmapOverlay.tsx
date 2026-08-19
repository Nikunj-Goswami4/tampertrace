import { useState, useRef } from 'react';
import { Layers, GripVertical } from 'lucide-react';
import { cn } from '../utils';

interface HeatmapOverlayProps {
  originalImageSrc: string | null;
  heatmapBase64: string | null;
  isPdf?: boolean;
}

export function HeatmapOverlay({ originalImageSrc, heatmapBase64, isPdf }: HeatmapOverlayProps) {
  const [sliderPosition, setSliderPosition] = useState(50);
  const [isDragging, setIsDragging] = useState(false);

  const heatmapSrc = heatmapBase64 ? `data:image/png;base64,${heatmapBase64}` : null;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2 transition-colors duration-300">
          <Layers className="w-5 h-5 text-blue-500" />
          Localization Heatmap
        </h3>

        {heatmapSrc && !isPdf && (
          <div className="text-sm font-medium text-slate-500 dark:text-slate-400">
            Drag slider to reveal tamper map
          </div>
        )}
      </div>

      <div className="relative w-full max-w-4xl mx-auto rounded-xl overflow-hidden bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-center min-h-[300px] select-none">
        {/* Base Image (if not PDF) */}
        {!isPdf && originalImageSrc && (
          <img
            src={originalImageSrc}
            alt="Original document"
            className="w-full h-auto object-contain max-h-[70vh] pointer-events-none"
          />
        )}

        {/* PDF Placeholder if no heatmap */}
        {isPdf && !heatmapSrc && (
          <div className="p-8 text-center text-slate-500 dark:text-slate-400">
            PDF Document Analyzed. No heatmap generated.
          </div>
        )}

        {/* Heatmap Overlay */}
        {heatmapSrc && (
          <div
            className={cn(
              "absolute inset-0 w-full h-full pointer-events-none flex items-center justify-center",
              isPdf ? "relative" : ""
            )}
            style={!isPdf ? { clipPath: `inset(0 ${100 - sliderPosition}% 0 0)` } : undefined}
          >
            <img
              src={heatmapSrc}
              alt="Tamper Heatmap"
              className={cn(
                "w-full h-auto object-contain max-h-[70vh]",
                (!isPdf && originalImageSrc) ? "absolute" : "relative",
                "opacity-80 mix-blend-multiply dark:mix-blend-screen"
              )}
            />
          </div>
        )}

        {/* Slider Handle UI */}
        {heatmapSrc && !isPdf && originalImageSrc && (
          <>
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-white shadow-[0_0_10px_rgba(0,0,0,0.5)] pointer-events-none z-10"
              style={{ left: `${sliderPosition}%` }}
            >
              <div className={cn(
                "absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 bg-white rounded-full shadow-lg flex items-center justify-center border border-slate-200 text-slate-600 transition-transform duration-200",
                isDragging ? "scale-110 shadow-xl" : "scale-100"
              )}>
                <GripVertical className="w-4 h-4" />
              </div>
            </div>

            <input
              type="range"
              min="0"
              max="100"
              value={sliderPosition}
              onChange={(e) => setSliderPosition(Number(e.target.value))}
              onMouseDown={() => setIsDragging(true)}
              onMouseUp={() => setIsDragging(false)}
              onTouchStart={() => setIsDragging(true)}
              onTouchEnd={() => setIsDragging(false)}
              className="absolute inset-0 w-full h-full opacity-0 cursor-ew-resize z-20"
            />
          </>
        )}

        {!heatmapSrc && !isPdf && originalImageSrc && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm">
            <span className="bg-white dark:bg-slate-800 px-4 py-2 rounded-full text-sm font-medium text-slate-600 dark:text-slate-300 shadow-sm border border-slate-200 dark:border-slate-700">
              No anomaly heatmap available for this document
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
