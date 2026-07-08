/** Scheduling API */
import { api } from "./client";
import type {
  CrewPosition,
  EligibleCrewmember,
  FlightLogCreate,
  FlightLogOut,
  ProposedSortie,
  SortieCreate,
  SortieFitness,
  SortieSummary,
  SuggestCrewResponse,
} from "./types";

export const applyCrewSuggestions = async (
  sortieId: number,
  payload: { person_id: number; crew_position: CrewPosition }[]
): Promise<{ assigned: FlightLogCreate[]; skipped: string[] }> => {
  const { data } = await api.post(`/api/scheduling/sorties/${sortieId}/apply-suggestions`, payload);
  return data;
};

export const assignCrew = async (
  sortieId: number,
  payload: FlightLogCreate
): Promise<FlightLogOut> => {
  const { data } = await api.post<FlightLogOut>(
    `/api/scheduling/sorties/${sortieId}/crew`,
    payload
  );
  return data;
};

export const createSortie = async (payload: SortieCreate): Promise<SortieSummary> => {
  const { data } = await api.post<SortieSummary>("/api/scheduling/sorties", payload);
  return data;
};

export const deleteSortie = async (id: number): Promise<void> => {
  await api.delete(`/api/scheduling/sorties/${id}`);
};

export const fetchEligibleCrew = async (
  sortieId: number,
  crewPosition: CrewPosition
): Promise<EligibleCrewmember[]> => {
  const { data } = await api.get<EligibleCrewmember[]>(
    `/api/scheduling/sorties/${sortieId}/eligible-crew`,
    { params: { crew_position: crewPosition } }
  );
  return data;
};

export const fetchSortieFitness = async (id: number): Promise<SortieFitness> => {
  const { data } = await api.get<SortieFitness>(`/api/scheduling/sorties/${id}/fitness`);
  return data;
};

export const fetchUpcomingSorties = async (): Promise<SortieSummary[]> => {
  const { data } = await api.get<SortieSummary[]>("/api/scheduling/sorties/upcoming");
  return data;
};

export const proposeWeek = async (body: {
  missions: {
    event_type?: string;
    event_code?: string;
    aircraft_id?: number;
    takeoff_time: string;
    land_time?: string;
    duration_hours?: number;
    positions?: CrewPosition[];
  }[];
}): Promise<{ proposals: ProposedSortie[] }> => {
  const { data } = await api.post<{ proposals: ProposedSortie[] }>(
    "/api/scheduling/propose-week",
    body
  );
  return data;
};

export const removeCrew = async (sortieId: number, flightLogId: number): Promise<void> => {
  await api.delete(`/api/scheduling/sorties/${sortieId}/crew/${flightLogId}`);
};

export const suggestCrew = async (sortieId: number): Promise<SuggestCrewResponse> => {
  const { data } = await api.post<SuggestCrewResponse>(
    `/api/scheduling/sorties/${sortieId}/suggest-crew`
  );
  return data;
};

