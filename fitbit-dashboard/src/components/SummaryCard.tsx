import { ReactNode } from "react";

interface SummaryCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: ReactNode;
  trend?: string;
  trendPositive?: boolean;
}

export default function SummaryCard({ title, value, subtitle, icon, trend, trendPositive }: SummaryCardProps) {
  return (
    <div className="relative overflow-hidden rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-sm hover:shadow-md transition-shadow group">
      <div className="absolute -top-10 -right-10 w-32 h-32 bg-blue-500/5 rounded-full blur-2xl group-hover:bg-blue-500/10 transition-colors"></div>
      
      <div className="flex justify-between items-start mb-4 relative z-10">
        <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 text-blue-500 dark:text-blue-400 ring-1 ring-slate-100 dark:ring-slate-700">
          {icon}
        </div>
        {trend && (
          <span className={`text-xs font-semibold px-2 py-1 rounded-full ${trendPositive === undefined ? 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400' : trendPositive ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400' : 'bg-rose-100 text-rose-700 dark:bg-rose-500/10 dark:text-rose-400'}`}>
            {trend}
          </span>
        )}
      </div>
      
      <div className="relative z-10">
        <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-1">{title}</h3>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">{value}</span>
          {subtitle && <span className="text-sm font-medium text-slate-500 dark:text-slate-400">{subtitle}</span>}
        </div>
      </div>
    </div>
  );
}
