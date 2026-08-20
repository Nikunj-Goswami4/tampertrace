import * as Accordion from '@radix-ui/react-accordion';
import { ChevronDown, Activity, FileSearch, Copy, Camera, Type } from 'lucide-react';
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

const truncateLongStrings = (_key: string, value: unknown) => {
  if (typeof value === 'string' && value.length > 200) {
    return `<string omitted for brevity (${value.length} characters)>`;
  }
  return value;
};

export function SignalBreakdown({ signals }: SignalBreakdownProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 transition-colors duration-300">Forensic Signals</h3>
      {/* Screen View (Interactive Accordions) */}
      <div className="print:hidden">
        <Accordion.Root type="multiple" className="grid gap-3">
          {signals.map((sig) => (
            <SignalCard key={sig.name} signal={sig} />
          ))}
        </Accordion.Root>
      </div>

      {/* Print View (Static List) */}
      <div className="hidden print:flex flex-col gap-4">
        {signals.map((sig) => (
          <PrintSignalCard key={`print-${sig.name}`} signal={sig} />
        ))}
      </div>
    </div>
  );
}

function SignalCard({ signal }: { signal: SignalResult }) {
  const meta = SIGNAL_META[signal.name] || { label: signal.name, icon: Activity, desc: 'Analysis module' };
  const Icon = meta.icon;

  // Score is 0 to 1
  const scorePct = Math.round(signal.score * 100);

  let scoreColor: string;
  let bgIconClass: string;
  if (scorePct > 65) {
    scoreColor = 'text-rose-600 dark:text-rose-400';
    bgIconClass = 'bg-rose-50 border-rose-100 text-rose-500 dark:bg-rose-900/30 dark:border-rose-800 dark:text-rose-400';
  } else if (scorePct < 30) {
    scoreColor = 'text-emerald-600 dark:text-emerald-400';
    bgIconClass = 'bg-emerald-50 border-emerald-100 text-emerald-500 dark:bg-emerald-900/30 dark:border-emerald-800 dark:text-emerald-400';
  } else {
    scoreColor = 'text-amber-600 dark:text-amber-400';
    bgIconClass = 'bg-slate-50 border-slate-100 text-slate-500 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-400';
  }

  return (
    <Accordion.Item
      value={signal.name}
      className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm hover:shadow transition-all duration-300"
    >
      <Accordion.Header className="flex">
        <Accordion.Trigger className="group flex-1 flex items-center justify-between p-4 focus:outline-none focus-visible:bg-slate-50 dark:focus-visible:bg-slate-800 transition-colors duration-300">
          <div className="flex items-center gap-4">
            <div className={cn("p-2 rounded-lg border transition-colors duration-300", bgIconClass)}>
              <Icon className="w-5 h-5" />
            </div>
            <div className="text-left">
              <h4 className="font-semibold text-slate-900 dark:text-white transition-colors duration-300">{meta.label}</h4>
              <p className="text-sm text-slate-500 dark:text-slate-400 hidden sm:block transition-colors duration-300">{meta.desc}</p>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <div className="text-right">
              <div className={cn("text-lg font-bold transition-colors duration-300", scoreColor)}>
                {scorePct}%
              </div>
              <div className="text-xs font-medium text-slate-400 dark:text-slate-500 uppercase tracking-wider transition-colors duration-300">Anomaly</div>
            </div>
            <div className="text-slate-400 dark:text-slate-500 transition-transform duration-300 group-data-[state=open]:rotate-180">
              <ChevronDown className="w-5 h-5" />
            </div>
          </div>
        </Accordion.Trigger>
      </Accordion.Header>

      <Accordion.Content className="overflow-hidden data-[state=closed]:animate-slideUp data-[state=open]:animate-slideDown">
        <div className="p-4 pt-0 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 transition-colors duration-300">
          <div className="mt-4 p-4 bg-slate-800 dark:bg-black/40 rounded-lg overflow-x-auto border border-slate-700/50">
            <pre className="text-xs text-slate-300 dark:text-slate-400 font-mono">
              {JSON.stringify(signal.details, truncateLongStrings, 2)}
            </pre>
          </div>
        </div>
      </Accordion.Content>
    </Accordion.Item>
  );
}

function PrintSignalCard({ signal }: { signal: SignalResult }) {
  const meta = SIGNAL_META[signal.name] || { label: signal.name, icon: Activity, desc: 'Analysis module' };
  const Icon = meta.icon;
  const scorePct = Math.round(signal.score * 100);

  return (
    <div className="border border-slate-200 rounded-xl p-4 flex flex-col gap-4 break-inside-avoid">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Icon className="w-5 h-5 text-slate-600" />
          <div>
            <h4 className="font-semibold text-slate-900">{meta.label}</h4>
            <p className="text-sm text-slate-500">{meta.desc}</p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-lg font-bold text-slate-900">{scorePct}%</div>
          <div className="text-xs font-medium text-slate-500 uppercase">Anomaly</div>
        </div>
      </div>
      <div className="bg-slate-50 border border-slate-100 p-3 rounded-lg text-xs font-mono text-slate-700 whitespace-pre-wrap break-all">
        {JSON.stringify(signal.details, truncateLongStrings, 2)}
      </div>
    </div>
  );
}
