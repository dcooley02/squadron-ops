/** Core dashboard / roster / sorties / logbook API */
import { api } from "./client";
import type {
  AircraftDetail,
  AircraftSummary,
  AuditLogEntry,
  CbrTaskOption,
  DashboardSummary,
  Discrepancy,
  PersonDetail,
  PersonSummary,
  SafetyReport,
  SortieCompletePayload,
  SortieDetail,
  SortieSummary,
  TrainingJacketEntry,
} from "./types";

export const completeSortie = async (
  sortieId: number,
  payload: SortieCompletePayload
): Promise<SortieDetail> => {
  const { data } = await api.post<SortieDetail>(
    `/api/logging/sorties/${sortieId}/complete`,
    payload
  );
  return data;
};

export const fetchAircraft = async (status?: string): Promise<AircraftSummary[]> => {
  const { data } = await api.get<AircraftSummary[]>("/api/aircraft", {
    params: status ? { status } : undefined,
  });
  return data;
};

export const fetchAircraftAdb = async (aircraftId: number): Promise<Discrepancy[]> => {
  const { data } = await api.get<Discrepancy[]>(
    `/api/logging/aircraft/${aircraftId}/adb`
  );
  return data;
};

export const fetchAircraftDetail = async (id: number): Promise<AircraftDetail> => {
  const { data } = await api.get<AircraftDetail>(`/api/aircraft/${id}`);
  return data;
};

export const fetchAuditLog = async (params?: {
  method?: string;
  path_contains?: string;
  limit?: number;
}): Promise<AuditLogEntry[]> => {
  const { data } = await api.get<AuditLogEntry[]>("/api/audit", { params });
  return data;
};

export const fetchCbrTaskOptions = async (): Promise<CbrTaskOption[]> => {
  const { data } = await api.get<CbrTaskOption[]>("/api/logging/tasks/options");
  return data;
};

export const fetchDashboardSummary = async (): Promise<DashboardSummary> => {
  const { data } = await api.get<DashboardSummary>("/api/dashboard/summary");
  return data;
};

export const fetchPerson = async (id: number): Promise<PersonDetail> => {
  const { data } = await api.get<PersonDetail>(`/api/persons/${id}`);
  return data;
};

export const fetchPersonTrainingJacket = async (personId: number): Promise<TrainingJacketEntry[]> => {
  const { data } = await api.get<TrainingJacketEntry[]>(
    `/api/logging/persons/${personId}/training-jacket`
  );
  return data;
};

export const fetchPersons = async (role?: string): Promise<PersonSummary[]> => {
  const { data } = await api.get<PersonSummary[]>("/api/persons", {
    params: role ? { role } : undefined,
  });
  return data;
};

export const fetchSafetyReportsForSortie = async (
  sortieId: number
): Promise<SafetyReport[]> => {
  const { data } = await api.get<SafetyReport[]>("/api/logging/safety/reports", {
    params: { sortie_id: sortieId },
  });
  return data;
};

export const fetchSortie = async (id: number): Promise<SortieDetail> => {
  const { data } = await api.get<SortieDetail>(`/api/sorties/${id}`);
  return data;
};

export const fetchSorties = async (
  params?: { date_from?: string; date_to?: string; limit?: number }
): Promise<SortieSummary[]> => {
  const { data } = await api.get<SortieSummary[]>("/api/sorties", { params });
  return data;
};

