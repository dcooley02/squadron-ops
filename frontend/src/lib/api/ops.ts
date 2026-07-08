/** SDO ops API */
import { api } from "./client";
import type { DayOps, SortieOpsStatus } from "./types";

export const fetchDayOps = async (opsDate: string): Promise<DayOps> => {
  const { data } = await api.get<DayOps>(`/api/ops/day/${opsDate}`);
  return data;
};

export const patchSortieOpsStatus = async (
  sortieId: number,
  body: {
    ops_status: SortieOpsStatus;
    mission_summary?: string;
    comm_plan?: string;
    brief_sheet_notes?: string;
  }
): Promise<void> => {
  await api.patch(`/api/ops/sorties/${sortieId}/status`, body);
};

export const publishSchedule = async (
  opsDate: string,
  body?: { published_by_person_id?: number; remarks?: string }
): Promise<DayOps["publication"]> => {
  const { data } = await api.post(`/api/ops/schedule/${opsDate}/publish`, body ?? {});
  return data;
};

