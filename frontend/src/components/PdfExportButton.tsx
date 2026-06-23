import { useState } from "react";
import { FileDown } from "lucide-react";
import clsx from "clsx";
import { pdfErrorMessage } from "../lib/pdf";

interface Props {
  label: string;
  onDownload: () => Promise<void>;
  className?: string;
  variant?: "button" | "link";
  showIcon?: boolean;
}

export default function PdfExportButton({
  label,
  onDownload,
  className,
  variant = "button",
  showIcon = true,
}: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    if (loading) return;
    setError(null);
    setLoading(true);
    try {
      await onDownload();
    } catch (err) {
      setError(pdfErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <span className={clsx("inline-flex flex-col", className)}>
      <button
        type="button"
        onClick={handleClick}
        disabled={loading}
        className={clsx(
          "disabled:opacity-50",
          variant === "link"
            ? "text-xs text-slate-400 hover:text-slate-200"
            : "inline-flex items-center gap-1 px-3 py-1.5 text-sm rounded border border-slate-700 hover:bg-slate-800 text-slate-300"
        )}
      >
        {showIcon && variant === "button" && <FileDown size={13} />}
        {loading ? "Exporting…" : label}
      </button>
      {error && (
        <span className="text-xs text-red-400 mt-1 max-w-xs" role="alert">
          {error}
        </span>
      )}
    </span>
  );
}