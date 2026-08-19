import { useState } from 'react';
import { ChevronDown, ChevronUp, Activity, FileSearch, Copy, Camera, Type } from 'lucide-react';
import { cn } from '../utils';

interface SignalResult {
  name: string;
  score: number;
  details: Record<string, unknown>;
}

interface SignalBreakdownProps {
  signals: SignalResult[];
}

const SIGNAL_META: Record<string, { label: string, icon: React.ElementType, desc: string }> = {
  trufor: { label: 'TruFor Pixel AI', icon: Activity, desc: 'Deep learning anomaly detection.' },
  ela: { label: 'Error Level Analysis', icon: FileSearch, desc: 'JPEG compression difference.' },
  copy_move: { label: 'Copy-Move', icon: Copy, desc: 'Clone region detection.' },
  exif: { label: 'EXIF Metadata', icon: Camera, desc: 'Software signatures & timestamps.' },
  ocr: { label: 'OCR Typography', icon: Type, desc: 'Text bounding box inconsistencies.' },
};

export function SignalBreakdown({ signals }: SignalBreakdownProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-slate-900 mb-4">Forensic Signals</h3>
      <div className="grid gap-3">
        {signals.map((sig) => (
          <SignalCard key={sig.name} signal={sig} />
        ))}
      </div>
    </div>
  );
}

function SignalCard({ signal }: { signal: SignalResult }) {
  const [expanded, setExpanded] = useState(false);
  const meta = SIGNAL_META[signal.name] || { label: signal.name, icon: Activity, desc: 'Analysis module' };
  const Icon = meta.icon;
  
  // Score is 0 to 1
  const scorePct = Math.round(signal.score * 100);
  
  // High score means highly tampered. 
  // Let's color code the score text.
  let scoreColor: string;
  if (scorePct > 65) scoreColor = 'text-rose-600';
  else if (scorePct < 30) scoreColor = 'text-emerald-600';
  else scoreColor = 'text-amber-600';

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm hover:shadow transition-shadow">
      <button 
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 focus:outline-none focus-visible:bg-slate-50"
      >
        <div className="flex items-center gap-4">
          <div className={cn("p-2 rounded-lg bg-slate-50 border border-slate-100", scorePct > 65 ? "bg-rose-50 border-rose-100 text-rose-500" : "text-slate-500")}>
            <Icon className="w-5 h-5" />
          </div>
          <div className="text-left">
            <h4 className="font-semibold text-slate-900">{meta.label}</h4>
            <p className="text-sm text-slate-500 hidden sm:block">{meta.desc}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-6">
          <div className="text-right">
            <div className={cn("text-lg font-bold", scoreColor)}>
              {scorePct}%
            </div>
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Anomaly</div>
          </div>
          <div className="text-slate-400">
            {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </div>
        </div>
      </button>

      {expanded && (
        <div className="p-4 pt-0 border-t border-slate-100 bg-slate-50/50">
          <div className="mt-4 p-4 bg-slate-800 rounded-lg overflow-x-auto">
            <pre className="text-xs text-slate-300 font-mono">
              {JSON.stringify(signal.details, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
