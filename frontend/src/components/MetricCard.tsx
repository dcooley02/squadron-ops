import { ReactNode } from "react";
import clsx from "clsx";

interface MetricCardProps {
  label: string;
  value: string | number;
  sublabel?: string;
  variant?: "default" | "warning" | "danger" | "good";
  icon?: ReactNode;
}

export default function MetricCard({
  label,
  value,
  sublabel,
  variant = "default",
  icon,
}: MetricCardProps) {
  return (
    <div
      className={clsx(
        "card",
        variant === "warning" && "border-yellow-600/50 bg-yellow-950/20",
        variant === "danger" && "border-red-600/50 bg-red-950/20",
        variant === "good" && "border-green-600/30",
      )}
    >
      <div className="flex items-start justify-between">
        <div className="text-xs font-medium text-slate-400 uppercase tracking-wide">
          {label}
        </div>
        {icon && <div className="text-slate-500">{icon}</div>}
      </div>
      <div
        className={clsx(
          "text-3xl font-semibold mt-2",
          variant === "warning" && "text-yellow-400",
          variant === "danger" && "text-red-400",
          variant === "good" && "text-green-400",
        )}
      >
        {value}
      </div>
      {sublabel && (
        <div className="text-xs text-slate-500 mt-1">{sublabel}</div>
      )}
    </div>
  );
}