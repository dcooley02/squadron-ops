/** Maintenance API */
import { api } from "./client";
import type {
  AircraftDetail,
  AircraftInspection,
  Discrepancy,
  DiscrepancySeverity,
  DiscrepancyWorkStatus,
  LogbookEntry,
  PhaseForecastRow,
  QaReleasePayload,
  ReleaseForecast,
  WorkCenter,
  WorkOrder,
} from "./types";

export const createDiscrepancy = async (
  aircraftId: number,
  body: {
    description: string;
    severity?: DiscrepancySeverity;
    system_affected?: string;
    notes?: string;
    type_wo_code?: string;
    work_center_id?: number;
  }
): Promise<Discrepancy> => {
  const { data } = await api.post<Discrepancy>(
    `/api/maintenance/aircraft/${aircraftId}/discrepancies`,
    body
  );
  return data;
};

export const fetchAircraftDiscrepancies = async (
  aircraftId: number,
  openOnly?: boolean
): Promise<Discrepancy[]> => {
  const { data } = await api.get<Discrepancy[]>(
    `/api/maintenance/aircraft/${aircraftId}/discrepancies`,
    { params: openOnly ? { open_only: true } : undefined }
  );
  return data;
};

export const fetchAircraftInspections = async (aircraftId: number): Promise<AircraftInspection[]> => {
  const { data } = await api.get<AircraftInspection[]>(
    `/api/maintenance/aircraft/${aircraftId}/inspections`
  );
  return data;
};

export const fetchLogbook = async (aircraftId: number): Promise<LogbookEntry[]> => {
  const { data } = await api.get<LogbookEntry[]>(
    `/api/maintenance/aircraft/${aircraftId}/logbook`
  );
  return data;
};

export const fetchPhaseForecast = async (
  weeklyFlightHours = 25
): Promise<PhaseForecastRow[]> => {
  const { data } = await api.get<PhaseForecastRow[]>("/api/maintenance/forecast/phase", {
    params: { weekly_flight_hours: weeklyFlightHours },
  });
  return data;
};

export const fetchReleaseForecast = async (aircraftId: number): Promise<ReleaseForecast> => {
  const { data } = await api.get<ReleaseForecast>(
    `/api/maintenance/forecast/release/${aircraftId}`
  );
  return data;
};

export const fetchWorkCenters = async (): Promise<WorkCenter[]> => {
  const { data } = await api.get<WorkCenter[]>("/api/maintenance/work-centers");
  return data;
};

export const fetchWorkOrders = async (aircraftId: number): Promise<WorkOrder[]> => {
  const { data } = await api.get<WorkOrder[]>(
    `/api/maintenance/aircraft/${aircraftId}/work-orders`
  );
  return data;
};

export const patchDiscrepancy = async (
  id: number,
  body: { work_status?: DiscrepancyWorkStatus; corrective_action?: string; system_affected?: string }
): Promise<Discrepancy> => {
  const { data } = await api.patch<Discrepancy>(`/api/maintenance/discrepancies/${id}`, body);
  return data;
};

export const patchInspection = async (
  aircraftId: number,
  inspectionId: number,
  body: {
    last_completed_date?: string;
    last_completed_hours?: number;
    last_completion_notes?: string;
  }
): Promise<AircraftInspection> => {
  const { data } = await api.patch<AircraftInspection>(
    `/api/maintenance/aircraft/${aircraftId}/inspections/${inspectionId}`,
    body
  );
  return data;
};

export const patchWorkOrder = async (
  workOrderId: number,
  body: {
    status?: DiscrepancyWorkStatus;
    corrective_action?: string;
    work_center_id?: number;
  }
): Promise<WorkOrder> => {
  const { data } = await api.patch<WorkOrder>(`/api/maintenance/work-orders/${workOrderId}`, body);
  return data;
};

export const qaRelease = async (
  aircraftId: number,
  body: QaReleasePayload
): Promise<AircraftDetail> => {
  const { data } = await api.post<AircraftDetail>(
    `/api/maintenance/aircraft/${aircraftId}/qa-release`,
    body
  );
  return data;
};

export const qaSignoffWorkOrder = async (
  workOrderId: number,
  body: { notes: string; release_eligible?: boolean }
): Promise<void> => {
  await api.post(`/api/maintenance/work-orders/${workOrderId}/qa-signoff`, body);
};

