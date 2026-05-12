import { useEffect, useState, type ReactNode } from "react";
import { format } from "date-fns";

interface Props {
  boardName: string;
  lastUpdatedAt?: number;
  children: ReactNode;
}

export default function BoardLayout({ boardName, lastUpdatedAt, children }: Props) {
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  const clockText = format(new Date(now), "HH:mm:ss");

  let updatedText = "—";
  if (lastUpdatedAt) {
    const secs = Math.round((now - lastUpdatedAt) / 1000);
    updatedText = secs < 5 ? "Updated just now" : `Updated ${secs}s ago`;
  }

  return (
    <div className="fixed inset-0 bg-slate-950 flex flex-col">
      {/* Top bar */}
      <div className="h-[60px] shrink-0 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-6">
        <div className="flex items-baseline gap-3">
          <span className="text-slate-500 text-sm font-medium tracking-widest uppercase">
            HSC Squadron Ops
          </span>
          <span className="text-slate-700">·</span>
          <span className="text-slate-200 text-base font-bold tracking-wider uppercase">
            {boardName}
          </span>
        </div>
        <div className="text-slate-200 text-2xl font-mono font-semibold tabular-nums tracking-wide">
          {clockText}
        </div>
      </div>

      {/* Content area — fills between bars */}
      <div className="flex-1 min-h-0 flex flex-col">
        {children}
      </div>

      {/* Bottom bar */}
      <div className="h-[40px] shrink-0 bg-slate-900 border-t border-slate-800 flex items-center justify-between px-6">
        <span className="text-slate-500 text-sm">{updatedText}</span>
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
          </span>
          <span className="text-slate-500 text-sm font-medium uppercase tracking-widest">
            Auto-Refresh On
          </span>
        </div>
      </div>
    </div>
  );
}
