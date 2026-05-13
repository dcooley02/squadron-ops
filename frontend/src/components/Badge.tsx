import clsx from "clsx";
import type { ReactNode } from "react";

type BadgeVariant = "neutral" | "success" | "warning" | "danger" | "info";

interface BadgeProps {
  variant?: BadgeVariant;
  children: ReactNode;
  className?: string;
}

const variantClasses: Record<BadgeVariant, string> = {
  neutral: "bg-slate-800 text-slate-300 border border-slate-700",
  success: "bg-green-950/50 text-green-400 border border-green-800/50",
  warning: "bg-yellow-950/50 text-yellow-400 border border-yellow-800/50",
  danger: "bg-red-950/50 text-red-400 border border-red-800/50",
  info: "bg-blue-950/50 text-blue-400 border border-blue-800/50",
};

export default function Badge({ variant = "neutral", children, className }: BadgeProps) {
  return (
    <span className={clsx("badge", variantClasses[variant], className)}>
      {children}
    </span>
  );
}