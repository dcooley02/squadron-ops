import type { ReactNode } from "react";

export default function Overlay({
  children,
  onClose,
}: {
  children: ReactNode;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div
        className="absolute inset-0"
        onClick={onClose}
        aria-hidden="true"
      />
      <div className="relative z-10 bg-slate-900 border border-slate-700 rounded-xl p-6 w-full max-w-md shadow-2xl">
        {children}
      </div>
    </div>
  );
}
