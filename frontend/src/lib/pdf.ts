import type { AxiosError } from "axios";
import { api } from "./api";

export const PDF_UNAVAILABLE_MSG =
  "PDF export is unavailable. Install WeasyPrint on the server (pip install weasyprint) and restart the API.";

export class PdfDownloadError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "PdfDownloadError";
  }
}

async function messageFromErrorBlob(data: Blob, status: number): Promise<string> {
  if (status === 503) return PDF_UNAVAILABLE_MSG;
  if (status === 401) return "Session expired — sign in again and retry.";
  try {
    const text = await data.text();
    const parsed = JSON.parse(text) as { detail?: string };
    if (typeof parsed.detail === "string" && parsed.detail.length > 0) {
      return parsed.detail;
    }
  } catch {
    // not JSON
  }
  return `PDF export failed (HTTP ${status}).`;
}

function triggerBrowserDownload(blob: Blob, filename: string): void {
  const blobUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = blobUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(blobUrl);
}

export async function downloadPdf(
  url: string,
  filename: string,
  params?: Record<string, string | number>
): Promise<void> {
  try {
    const response = await api.get(url, { responseType: "blob", params });
    const contentType = String(response.headers["content-type"] ?? "");
    if (!contentType.includes("pdf")) {
      const msg = await messageFromErrorBlob(response.data as Blob, response.status);
      throw new PdfDownloadError(msg);
    }
    triggerBrowserDownload(response.data as Blob, filename);
  } catch (err) {
    if (err instanceof PdfDownloadError) throw err;
    const axiosErr = err as AxiosError<Blob>;
    if (axiosErr.response) {
      const { status, data } = axiosErr.response;
      const msg =
        data instanceof Blob
          ? await messageFromErrorBlob(data, status)
          : `PDF export failed (HTTP ${status}).`;
      throw new PdfDownloadError(msg);
    }
    if (axiosErr.code === "ERR_NETWORK") {
      throw new PdfDownloadError("Cannot reach the API — is the backend running on :8001?");
    }
    throw new PdfDownloadError("PDF export failed unexpectedly.");
  }
}

export function pdfErrorMessage(err: unknown): string {
  if (err instanceof PdfDownloadError) return err.message;
  if (err instanceof Error && err.message) return err.message;
  return PDF_UNAVAILABLE_MSG;
}

export const downloadAtoPdf = (opsDate: string): Promise<void> =>
  downloadPdf(`/api/ops/day/${opsDate}/ato.pdf`, `ato_${opsDate}.pdf`);

export const downloadBriefSheetPdf = (sortieId: number): Promise<void> =>
  downloadPdf(`/api/ops/sorties/${sortieId}/brief-sheet.pdf`, `brief_sheet_${sortieId}.pdf`);

export const downloadGradecardPdf = (gradecardId: number): Promise<void> =>
  downloadPdf(`/api/syllabus/gradecards/${gradecardId}/pdf`, `gradecard_${gradecardId}.pdf`);

export const downloadReadinessBriefPdf = (): Promise<void> =>
  downloadPdf("/api/readiness/squadron/brief.pdf", "readiness_brief.pdf");