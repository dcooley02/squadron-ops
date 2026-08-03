import { useState, type ReactNode } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

export function Section({
  title,
  badge,
  required,
  defaultOpen = false,
  children,
}: {
  title: string;
  badge?: ReactNode;
  required?: boolean;
  defaultOpen?: boolean;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="card">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex items-center justify-between w-full text-left"
      >
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-semibold text-slate-100">{title}</span>
          {required && (
            <span className="text-xs text-blue-400 font-medium uppercase tracking-wide">
              Required
            </span>
          )}
          {badge}
        </div>
        {open ? (
          <ChevronUp size={16} className="text-slate-400 shrink-0" />
        ) : (
          <ChevronDown size={16} className="text-slate-400 shrink-0" />
        )}
      </button>
      {open && <div className="mt-4 space-y-4">{children}</div>}
    </div>
  );
}

export function Lbl({ children }: { children: ReactNode }) {
  return <label className="block text-xs text-slate-400 mb-1">{children}</label>;
}

export const INPUT_CLS =
  "w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-slate-500";
