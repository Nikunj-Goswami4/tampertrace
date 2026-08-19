import { ShieldCheck, ShieldAlert, AlertTriangle } from 'lucide-react';
import { cn } from '../utils';

interface VerdictBadgeProps {
  verdict: string;
  confidence: number;
}

export function VerdictBadge({ verdict, confidence }: VerdictBadgeProps) {
  let colorClass: string;
  let bgClass: string;
  let barClass: string;
  let Icon: React.ElementType;

  switch (verdict.toLowerCase()) {
    case 'authentic':
      colorClass = 'text-emerald-700 dark:text-emerald-400';
      bgClass = 'bg-emerald-50 border-emerald-200 dark:bg-emerald-900/20 dark:border-emerald-800/50';
      barClass = 'bg-emerald-500 dark:shadow-[0_0_15px_rgba(52,211,153,0.5)]';
      Icon = ShieldCheck;
      break;
    case 'likely tampered':
      colorClass = 'text-rose-700 dark:text-rose-400';
      bgClass = 'bg-rose-50 border-rose-200 dark:bg-rose-900/20 dark:border-rose-800/50';
      barClass = 'bg-rose-500 dark:shadow-[0_0_15px_rgba(251,113,133,0.5)]';
      Icon = ShieldAlert;
      break;
    case 'uncertain':
    default:
      colorClass = 'text-amber-700 dark:text-amber-400';
      bgClass = 'bg-amber-50 border-amber-200 dark:bg-amber-900/20 dark:border-amber-800/50';
      barClass = 'bg-amber-500 dark:shadow-[0_0_15px_rgba(251,191,36,0.5)]';
      Icon = AlertTriangle;
      break;
  }

  return (
    <div className={cn("rounded-2xl border p-6 shadow-sm flex flex-col gap-4 transition-colors duration-300", bgClass)}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className={cn("p-2 rounded-xl bg-white/60 dark:bg-black/20 shadow-sm transition-colors duration-300", colorClass)}>
            <Icon className="w-6 h-6" strokeWidth={2} />
          </div>
          <div>
            <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-0.5 transition-colors duration-300">
              System Verdict
            </h3>
            <p className={cn("text-2xl font-semibold tracking-tight transition-colors duration-300", colorClass)}>
              {verdict}
            </p>
          </div>
        </div>
        
        <div className="text-right">
          <div className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white transition-colors duration-300">
            {confidence.toFixed(1)}%
          </div>
          <div className="text-sm font-medium text-slate-500 dark:text-slate-400 transition-colors duration-300">Confidence</div>
        </div>
      </div>

      <div className="w-full bg-white/60 dark:bg-black/20 rounded-full h-2 overflow-hidden shadow-inner transition-colors duration-300">
        <div 
          className={cn("h-full transition-all duration-1000 ease-out", barClass)}
          style={{ width: `${Math.max(0, Math.min(100, confidence))}%` }}
        />
      </div>
    </div>
  );
}
