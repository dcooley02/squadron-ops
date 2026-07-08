/**
 * API client public surface. Domain modules live alongside this index.
 * Imports of `../lib/api` resolve here.
 */
export { api, API_BASE_URL } from "./client";
export * from "./types";
export * from "./auth";
export * from "./core";
export * from "./scheduling";
export * from "./training";
export * from "./currency";
export * from "./maintenance";
export * from "./readiness";
export * from "./boards";
export * from "./ops";
export {
  downloadReadinessBriefPdf,
  downloadAtoPdf,
  downloadBriefSheetPdf,
  downloadGradecardPdf,
  pdfErrorMessage,
  PDF_UNAVAILABLE_MSG,
} from "../pdf";
