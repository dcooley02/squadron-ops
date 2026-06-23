import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { CheckCircle, XCircle, X } from "lucide-react";
import clsx from "clsx";

type ToastVariant = "success" | "error";

interface ToastMessage {
  id: number;
  text: string;
  variant: ToastVariant;
}

interface ToastContextValue {
  showToast: (text: string, variant?: ToastVariant) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

let toastId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = useCallback((text: string, variant: ToastVariant = "success") => {
    const id = ++toastId;
    setToasts((prev) => [...prev, { id, text, variant }]);
  }, []);

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed bottom-20 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
        {toasts.map((t) => (
          <ToastItem key={t.id} toast={t} onDismiss={() => dismiss(t.id)} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

function ToastItem({ toast, onDismiss }: { toast: ToastMessage; onDismiss: () => void }) {
  useEffect(() => {
    const timer = window.setTimeout(onDismiss, 4500);
    return () => window.clearTimeout(timer);
  }, [onDismiss]);

  return (
    <div
      className={clsx(
        "pointer-events-auto flex items-start gap-2.5 px-4 py-3 rounded-lg border shadow-xl max-w-sm",
        toast.variant === "success"
          ? "bg-green-950/95 border-green-700/50 text-green-100"
          : "bg-red-950/95 border-red-700/50 text-red-100"
      )}
      role="status"
    >
      {toast.variant === "success" ? (
        <CheckCircle size={18} className="text-green-400 shrink-0 mt-0.5" />
      ) : (
        <XCircle size={18} className="text-red-400 shrink-0 mt-0.5" />
      )}
      <p className="text-sm flex-1">{toast.text}</p>
      <button
        type="button"
        onClick={onDismiss}
        className="text-slate-400 hover:text-slate-200 shrink-0"
        aria-label="Dismiss"
      >
        <X size={14} />
      </button>
    </div>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}