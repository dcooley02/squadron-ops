import { api } from "./api";
import { downloadPdf } from "./pdf";
import type {
  LogbookFilters,
  LogbookResponse,
  SortieDetailFull,
} from "../types/logbook";

// ── Logbook JSON endpoint ────────────────────────────────────────────────────

export async function fetchLogbook(
  personId: number,
  filters: LogbookFilters
): Promise<LogbookResponse> {
  const params: Record<string, string | number> = {};
  if (filters.date_from) params.date_from = filters.date_from;
  if (filters.date_to) params.date_to = filters.date_to;
  if (filters.aircraft_id != null) params.aircraft_id = filters.aircraft_id;
  if (filters.event_code) params.event_code = filters.event_code;
  if (filters.crew_position) params.crew_position = filters.crew_position;
  if (filters.flight_mode) params.flight_mode = filters.flight_mode;
  const { data } = await api.get<LogbookResponse>(
    `/api/logging/logbook/${personId}`,
    { params }
  );
  return data;
}

// ── Full sortie detail (for LogbookEntryDetail modal) ────────────────────────

export async function fetchSortieDetail(sortieId: number): Promise<SortieDetailFull> {
  const { data } = await api.get<SortieDetailFull>(`/api/sorties/${sortieId}`);
  return data;
}

// ── PDF downloads ────────────────────────────────────────────────────────────

export async function downloadLogbookPdf(
  personId: number,
  lastName: string,
  firstInitial: string
): Promise<void> {
  await downloadPdf(
    `/api/logging/logbook/${personId}/pdf`,
    `logbook_${lastName}_${firstInitial}.pdf`
  );
}

export async function downloadLogbookPdfFiltered(
  personId: number,
  filters: LogbookFilters,
  lastName: string,
  firstInitial: string
): Promise<void> {
  const params: Record<string, string | number> = {};
  if (filters.date_from) params.date_from = filters.date_from;
  if (filters.date_to) params.date_to = filters.date_to;
  if (filters.aircraft_id != null) params.aircraft_id = filters.aircraft_id;
  if (filters.event_code) params.event_code = filters.event_code;
  if (filters.crew_position) params.crew_position = filters.crew_position;
  if (filters.flight_mode) params.flight_mode = filters.flight_mode;
  await downloadPdf(
    `/api/logging/logbook/${personId}/pdf/filtered`,
    `logbook_${lastName}_${firstInitial}_filtered.pdf`,
    params
  );
}
