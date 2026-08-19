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
      colorClass = 'text-emerald-700';
      bgClass = 'bg-emerald-50 border-emerald-200';
      barClass = 'bg-emerald-500';
      Icon = ShieldCheck;
      break;
    case 'likely tampered':
      colorClass = 'text-rose-700';
      bgClass = 'bg-rose-50 border-rose-200';
      barClass = 'bg-rose-500';
      Icon = ShieldAlert;
      break;
    case 'uncertain':
    default:
      colorClass = 'text-amber-700';
      bgClass = 'bg-amber-50 border-amber-200';
      barClass = 'bg-amber-500';
      Icon = AlertTriangle;
      break;
  }

  return (
    <div className={cn("rounded-2xl border p-6 shadow-sm flex flex-col gap-4", bgClass)}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className={cn("p-2 rounded-xl bg-white/60 shadow-sm", colorClass)}>
            <Icon className="w-6 h-6" strokeWidth={2} />
          </div>
          <div>
            <h3 className="text-sm font-medium text-slate-500 uppercase tracking-wider mb-0.5">
              System Verdict
            </h3>
            <p className={cn("text-2xl font-semibold tracking-tight", colorClass)}>
              {verdict}
            </p>
          </div>
        </div>
        
        <div className="text-right">
          <div className="text-3xl font-bold tracking-tight text-slate-900">
            {confidence.toFixed(1)}%
          </div>
          <div className="text-sm font-medium text-slate-500">Confidence</div>
        </div>
      </div>

      <div className="w-full bg-white/60 rounded-full h-2 overflow-hidden shadow-inner">
        <div 
          className={cn("h-full transition-all duration-1000 ease-out", barClass)}
          style={{ width: `${Math.max(0, Math.min(100, confidence))}%` }}
        />
      </div>
    </div>
  );
}
